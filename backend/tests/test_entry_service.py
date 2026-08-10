import json
from uuid import uuid4

import pytest

from app.domain.color import fallback_color
from app.domain.entities import Category
from app.domain.llm_client import ChatMessage, LLMError
from app.infra.db.repositories import SqlAlchemyEntryRepository, SqlAlchemyTagRepository
from app.infra.db.unit_of_work import SqlAlchemyUnitOfWork
from app.services.entry_service import EntryService
from app.services.tagging_service import TaggingResult, TaggingService, TagSuggestion
from app.services.text_correction_service import TextCorrectionService


def make_result(
    topic: str,
    subtopic: str | None = None,
    tags: tuple[str, ...] = (),
    quote: str | None = None,
    category: Category = Category.OTHER,
) -> TaggingResult:
    return TaggingResult(
        topic=TagSuggestion(name=topic, color=fallback_color(topic), category=category),
        subtopic=TagSuggestion(name=subtopic, color=fallback_color(subtopic), category=category)
        if subtopic
        else None,
        tags=[TagSuggestion(name=t, color=fallback_color(t), category=category) for t in tags],
        quote=quote,
    )


class StubLLMClient:
    def __init__(self, result: TaggingResult):
        self.result = result
        self.calls: list[list[ChatMessage]] = []

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        self.calls.append(messages)

        def ser(s: TagSuggestion) -> dict:
            return {"name": s.name, "color": s.color, "category": s.category.value}

        return json.dumps(
            {
                "topic": ser(self.result.topic),
                "subtopic": ser(self.result.subtopic) if self.result.subtopic else None,
                "tags": [ser(t) for t in self.result.tags],
                "quote": self.result.quote,
            }
        )


class CorrectionStubLLMClient:
    def __init__(self, corrected: str):
        self.corrected = corrected
        self.calls: list[list[ChatMessage]] = []

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        self.calls.append(messages)
        return json.dumps({"corrected": self.corrected})


def make_service(session, result: TaggingResult) -> EntryService:
    return EntryService(
        entry_repo=SqlAlchemyEntryRepository(session),
        tag_repo=SqlAlchemyTagRepository(session),
        tagging_service=TaggingService(StubLLMClient(result)),
        text_correction_service=TextCorrectionService(StubLLMClient(result)),
        uow=SqlAlchemyUnitOfWork(session),
    )


async def test_create_entry_tags_and_persists(session):
    service = make_service(
        session, make_result("работа", subtopic="дедлайны", tags=("стресс",), quote="успею")
    )

    entry = await service.create_entry("надо успеть до пятницы", source="web")

    assert entry.raw_text == "надо успеть до пятницы"
    assert entry.quote == "успею"
    tag_names = {t.tag.canonical_name for t in entry.tags}
    assert tag_names == {"работа", "дедлайны", "стресс"}
    assert all(t.tag.color.startswith("#") for t in entry.tags)


async def test_create_entry_reuses_existing_tag(session):
    service = make_service(session, make_result("работа"))

    first = await service.create_entry("первая мысль", source="web")
    second = await service.create_entry("вторая мысль", source="web")

    first_topic_id = next(t.tag.id for t in first.tags if t.tag.canonical_name == "работа")
    second_topic_id = next(t.tag.id for t in second.tags if t.tag.canonical_name == "работа")
    assert first_topic_id == second_topic_id


async def test_create_entry_keeps_first_color_on_reuse(session):
    first_service = make_service(session, make_result("работа"))
    await first_service.create_entry("первая мысль", source="web")
    first_color = (await first_service.create_entry("снова", source="web")).tags[0].tag.color

    other_result = TaggingResult(
        topic=TagSuggestion(name="работа", color="#000000", category=Category.OTHER),
        subtopic=None,
        tags=[],
    )
    other_service = make_service(session, other_result)
    entry = await other_service.create_entry("третья", source="web")

    assert entry.tags[0].tag.color == first_color
    assert entry.tags[0].tag.color != "#000000"


async def test_list_entries_filters_by_tag(session):
    service = make_service(session, make_result("учёба"))
    await service.create_entry("экзамен скоро", source="web")

    other_service = make_service(session, make_result("спорт"))
    await other_service.create_entry("пробежка", source="web")

    all_entries = await service.list_entries(
        tag_ids=None, date_from=None, date_to=None, limit=50, offset=0
    )
    assert len(all_entries) == 2

    study_tag_id = next(
        t.tag.id for e in all_entries for t in e.tags if t.tag.canonical_name == "учёба"
    )
    filtered = await service.list_entries(
        tag_ids=[study_tag_id], date_from=None, date_to=None, limit=50, offset=0
    )
    assert len(filtered) == 1
    assert filtered[0].raw_text == "экзамен скоро"


async def test_list_entries_multi_tag_filter_is_or_not_and(session):
    service = make_service(session, make_result("работа", tags=("срочное",)))
    both = await service.create_entry("горящий дедлайн", source="web")

    only_work_service = make_service(session, make_result("работа"))
    only_work = await only_work_service.create_entry("обычный рабочий день", source="web")

    only_urgent_service = make_service(session, make_result("срочное"))
    only_urgent = await only_urgent_service.create_entry("что-то ещё срочное", source="web")

    unrelated_service = make_service(session, make_result("сон"))
    await unrelated_service.create_entry("вздремнул", source="web")

    work_tag_id = next(t.tag.id for t in both.tags if t.tag.canonical_name == "работа")
    urgent_tag_id = next(t.tag.id for t in both.tags if t.tag.canonical_name == "срочное")

    filtered = await service.list_entries(
        tag_ids=[work_tag_id, urgent_tag_id],
        date_from=None,
        date_to=None,
        limit=50,
        offset=0,
    )

    assert {e.id for e in filtered} == {both.id, only_work.id, only_urgent.id}


async def test_list_entries_search_matches_raw_text(session):
    service = make_service(session, make_result("x"))
    await service.create_entry("надо сходить в спортзал сегодня", source="web")
    await service.create_entry("купить молоко", source="web")

    filtered = await service.list_entries(
        tag_ids=None, date_from=None, date_to=None, limit=50, offset=0, search="спортзал"
    )

    assert len(filtered) == 1
    assert "спортзал" in filtered[0].raw_text


async def test_get_entry_returns_none_when_missing(session):
    service = make_service(session, make_result("x"))
    assert await service.get_entry(uuid4()) is None


async def test_get_entry_roundtrip(session):
    service = make_service(session, make_result("x"))
    created = await service.create_entry("исходный текст", source="web")

    fetched = await service.get_entry(created.id)

    assert fetched is not None
    assert fetched.raw_text == "исходный текст"


async def test_update_entry_changes_text_keeps_tags(session):
    service = make_service(session, make_result("работа"))
    created = await service.create_entry("опечатка тут", source="web")
    original_tag_ids = {t.tag.id for t in created.tags}
    assert created.edited_at is None

    updated = await service.update_entry(created.id, "опечатка исправлена")

    assert updated is not None
    assert updated.raw_text == "опечатка исправлена"
    assert {t.tag.id for t in updated.tags} == original_tag_ids
    assert updated.edited_at is not None


async def test_update_entry_returns_none_when_missing(session):
    service = make_service(session, make_result("x"))
    assert await service.update_entry(uuid4(), "текст") is None


async def test_delete_entry_removes_it(session):
    service = make_service(session, make_result("x"))
    created = await service.create_entry("удали меня", source="web")

    deleted = await service.delete_entry(created.id)

    assert deleted is True
    assert await service.get_entry(created.id) is None


async def test_delete_entry_returns_false_when_missing(session):
    service = make_service(session, make_result("x"))
    assert await service.delete_entry(uuid4()) is False


async def test_retag_entry_replaces_tags(session):
    service = make_service(session, make_result("старая-тема"))
    created = await service.create_entry("текст заметки", source="web")
    assert {t.tag.canonical_name for t in created.tags} == {"старая-тема"}

    retag_service = make_service(session, make_result("новая-тема", tags=("свежий",)))
    retagged = await retag_service.retag_entry(created.id)

    assert retagged is not None
    assert retagged.raw_text == "текст заметки"
    assert {t.tag.canonical_name for t in retagged.tags} == {"новая-тема", "свежий"}


async def test_retag_entry_returns_none_when_missing(session):
    service = make_service(session, make_result("x"))
    assert await service.retag_entry(uuid4()) is None


def _unused_correction() -> TextCorrectionService:
    return TextCorrectionService(StubLLMClient(make_result("x")))


async def test_retag_entry_raises_instead_of_falling_back(session):
    entry_repo = SqlAlchemyEntryRepository(session)
    tag_repo = SqlAlchemyTagRepository(session)
    uow = SqlAlchemyUnitOfWork(session)
    service = EntryService(
        entry_repo,
        tag_repo,
        TaggingService(StubLLMClient(make_result("x"))),
        _unused_correction(),
        uow,
    )
    created = await service.create_entry("текст", source="web")

    failing_service = EntryService(
        entry_repo, tag_repo, TaggingService(_RaisingLLMClient()), _unused_correction(), uow
    )
    with pytest.raises(LLMError):
        await failing_service.retag_entry(created.id)


class _RaisingLLMClient:
    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        raise LLMError("роутер недоступен")


async def test_fallback_tag_not_offered_to_llm_as_existing(session):
    entry_repo = SqlAlchemyEntryRepository(session)
    tag_repo = SqlAlchemyTagRepository(session)
    uow = SqlAlchemyUnitOfWork(session)

    failing_service = EntryService(
        entry_repo, tag_repo, TaggingService(_RaisingLLMClient()), _unused_correction(), uow
    )
    fallback_entry = await failing_service.create_entry("текст", source="web")
    assert {t.tag.canonical_name for t in fallback_entry.tags} == {"не разобрано"}

    stub = StubLLMClient(make_result("работа"))
    other_service = EntryService(
        entry_repo, tag_repo, TaggingService(stub), _unused_correction(), uow
    )
    await other_service.create_entry("рабочие дела", source="web")

    sent_prompt = stub.calls[0][1].content
    assert "не разобрано" not in sent_prompt


async def test_create_entry_applies_correction_before_tagging_when_requested(session):
    entry_repo = SqlAlchemyEntryRepository(session)
    tag_repo = SqlAlchemyTagRepository(session)
    uow = SqlAlchemyUnitOfWork(session)
    correction = TextCorrectionService(CorrectionStubLLMClient("Привет, мир."))
    service = EntryService(
        entry_repo, tag_repo, TaggingService(StubLLMClient(make_result("x"))), correction, uow
    )

    entry = await service.create_entry("привет мир", source="web", correct_text=True)

    assert entry.raw_text == "Привет, мир."


async def test_create_entry_without_correction_flag_keeps_raw_text_untouched(session):
    service = make_service(session, make_result("x"))

    entry = await service.create_entry("текст без правок", source="web")

    assert entry.raw_text == "текст без правок"


async def test_update_entry_applies_correction_when_requested(session):
    entry_repo = SqlAlchemyEntryRepository(session)
    tag_repo = SqlAlchemyTagRepository(session)
    uow = SqlAlchemyUnitOfWork(session)
    correction = TextCorrectionService(CorrectionStubLLMClient("Исправленный текст."))
    service = EntryService(
        entry_repo, tag_repo, TaggingService(StubLLMClient(make_result("x"))), correction, uow
    )
    created = await service.create_entry("исходный текст", source="web")

    updated = await service.update_entry(created.id, "исправленный текст", correct_text=True)

    assert updated is not None
    assert updated.raw_text == "Исправленный текст."
