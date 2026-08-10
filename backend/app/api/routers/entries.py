from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, EntryServiceDep
from app.api.schemas.entry import EntryCreateRequest, EntryOut, EntryUpdateRequest
from app.domain.llm_client import LLMError

router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.post("", response_model=EntryOut, status_code=201)
async def create_entry(
    body: EntryCreateRequest, _: CurrentUser, entry_service: EntryServiceDep
) -> EntryOut:
    entry = await entry_service.create_entry(
        raw_text=body.text, source=body.source, correct_text=body.correct_text
    )
    return EntryOut.from_domain(entry)


@router.get("", response_model=list[EntryOut])
async def list_entries(
    _: CurrentUser,
    entry_service: EntryServiceDep,
    tag_ids: list[UUID] = Query(default=[]),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[EntryOut]:
    entries = await entry_service.list_entries(
        tag_ids=tag_ids or None,
        date_from=date_from,
        date_to=date_to,
        search=search or None,
        limit=limit,
        offset=offset,
    )
    return [EntryOut.from_domain(e) for e in entries]


@router.get("/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: UUID, _: CurrentUser, entry_service: EntryServiceDep) -> EntryOut:
    entry = await entry_service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
    return EntryOut.from_domain(entry)


@router.patch("/{entry_id}", response_model=EntryOut)
async def update_entry(
    entry_id: UUID, body: EntryUpdateRequest, _: CurrentUser, entry_service: EntryServiceDep
) -> EntryOut:
    entry = await entry_service.update_entry(entry_id, body.text, correct_text=body.correct_text)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
    return EntryOut.from_domain(entry)


@router.post("/{entry_id}/retag", response_model=EntryOut)
async def retag_entry(entry_id: UUID, _: CurrentUser, entry_service: EntryServiceDep) -> EntryOut:
    try:
        entry = await entry_service.retag_entry(entry_id)
    except LLMError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, f"Не удалось связаться с LLM-роутером: {exc}"
        ) from exc
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
    return EntryOut.from_domain(entry)


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: UUID, _: CurrentUser, entry_service: EntryServiceDep) -> None:
    deleted = await entry_service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Запись не найдена")
