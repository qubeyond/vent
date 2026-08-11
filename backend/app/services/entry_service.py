from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from pydantic import ValidationError

from app.domain.entities import Entry, EntryStatus, ProcessingStage, TagKind
from app.domain.llm_client import LLMError
from app.domain.repositories import EntryRepository, TagRepository
from app.domain.unit_of_work import UnitOfWork
from app.services.tagging_service import FALLBACK_TOPIC_NAME, TaggingResult, TaggingService
from app.services.text_correction_service import TextCorrectionService


class EntryService:
    def __init__(
        self,
        entry_repo: EntryRepository,
        tag_repo: TagRepository,
        tagging_service: TaggingService,
        text_correction_service: TextCorrectionService,
        uow: UnitOfWork,
    ):
        self._entry_repo = entry_repo
        self._tag_repo = tag_repo
        self._tagging_service = tagging_service
        self._text_correction_service = text_correction_service
        self._uow = uow

    async def create_entry(self, raw_text: str, source: str) -> Entry:
        entry = await self._entry_repo.add(
            raw_text=raw_text, source=source, status=EntryStatus.PROCESSING
        )
        await self._uow.commit()
        return entry

    async def process_entry(self, entry_id: UUID, correct_text: bool) -> None:
        entry = await self._entry_repo.get_by_id(entry_id)
        if entry is None:
            return

        raw_text = entry.raw_text
        if correct_text:
            await self._entry_repo.set_stage(entry_id, ProcessingStage.CORRECTING)
            await self._uow.commit()
            raw_text = await self._text_correction_service.correct(raw_text)

        await self._entry_repo.set_stage(entry_id, ProcessingStage.TAGGING)
        await self._uow.commit()
        result = await self._tagging_service.tag_entry(raw_text, await self._existing_tag_names())
        tag_ids_with_confidence = await self._resolve_tag_ids(result)

        await self._entry_repo.finish_processing(
            entry_id,
            raw_text=raw_text,
            quote=result.quote,
            tag_ids_with_confidence=tag_ids_with_confidence,
        )
        await self._uow.commit()

    async def start_retag(self, entry_id: UUID) -> Entry | None:
        entry = await self._entry_repo.mark_processing(entry_id)
        if entry is not None:
            await self._uow.commit()
        return entry

    async def process_retag(self, entry_id: UUID) -> None:
        entry = await self._entry_repo.get_by_id(entry_id)
        if entry is None:
            return

        await self._entry_repo.set_stage(entry_id, ProcessingStage.TAGGING)
        await self._uow.commit()

        try:
            result = await self._tagging_service.tag_entry_strict(
                entry.raw_text, await self._existing_tag_names()
            )
        except LLMError as exc:
            await self._entry_repo.mark_processing_failed(
                entry_id, f"Не удалось связаться с LLM-роутером: {exc}"
            )
            await self._uow.commit()
            return
        except (json.JSONDecodeError, ValidationError) as exc:
            await self._entry_repo.mark_processing_failed(
                entry_id, f"Не удалось разобрать ответ модели: {exc}"
            )
            await self._uow.commit()
            return

        tag_ids_with_confidence = await self._resolve_tag_ids(result)
        await self._entry_repo.finish_retag(entry_id, tag_ids_with_confidence)
        await self._uow.commit()

    async def list_entries(
        self,
        tag_ids: list[UUID] | None,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> list[Entry]:
        return await self._entry_repo.list_(
            tag_ids=tag_ids,
            date_from=date_from,
            date_to=date_to,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def get_entry(self, entry_id: UUID) -> Entry | None:
        return await self._entry_repo.get_by_id(entry_id)

    async def update_entry(
        self, entry_id: UUID, raw_text: str, correct_text: bool = False
    ) -> Entry | None:
        entry = await self._entry_repo.update_raw_text(entry_id, raw_text)
        if entry is None:
            return None
        if correct_text:
            entry = await self._entry_repo.mark_processing(entry_id)
        await self._uow.commit()
        return entry

    async def process_update_correction(self, entry_id: UUID) -> None:
        entry = await self._entry_repo.get_by_id(entry_id)
        if entry is None:
            return
        await self._entry_repo.set_stage(entry_id, ProcessingStage.CORRECTING)
        await self._uow.commit()
        corrected = await self._text_correction_service.correct(entry.raw_text)
        await self._entry_repo.finish_correction(entry_id, corrected)
        await self._uow.commit()

    async def delete_entry(self, entry_id: UUID) -> bool:
        deleted = await self._entry_repo.delete(entry_id)
        if deleted:
            await self._uow.commit()
        return deleted

    async def _existing_tag_names(self) -> list[str]:
        existing_by_usage = await self._tag_repo.list_with_counts(None, None)
        return [
            tag.canonical_name
            for tag, _count in existing_by_usage
            if tag.canonical_name != FALLBACK_TOPIC_NAME
        ]

    async def _resolve_tag_ids(self, result: TaggingResult) -> list[tuple[UUID, float | None]]:
        resolved: dict[UUID, None] = {}
        topic_tag = await self._tag_repo.get_or_create(
            result.topic.name, TagKind.TOPIC, result.topic.color, result.topic.category
        )
        resolved[topic_tag.id] = None
        if result.subtopic:
            subtopic_tag = await self._tag_repo.get_or_create(
                result.subtopic.name, TagKind.TAG, result.subtopic.color, result.subtopic.category
            )
            resolved[subtopic_tag.id] = None
        for suggestion in result.tags:
            tag = await self._tag_repo.get_or_create(
                suggestion.name, TagKind.TAG, suggestion.color, suggestion.category
            )
            resolved[tag.id] = None
        return [(tag_id, None) for tag_id in resolved]
