import json

import pytest
from pydantic import ValidationError

from app.domain.entities import Category
from app.domain.llm_client import ChatMessage, LLMError
from app.services.tagging_service import TaggingService


class RawLLMClient:
    def __init__(self, response: str | None = None, raises: Exception | None = None):
        self._response = response
        self._raises = raises

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        if self._raises is not None:
            raise self._raises
        assert json_mode is True
        return self._response


async def test_tag_entry_parses_and_normalizes():
    raw = json.dumps(
        {
            "topic": {"name": " Работа ", "color": "#7C3AED", "category": "карьера"},
            "subtopic": {"name": "Дедлайны", "color": "#0ea5e9", "category": "карьера"},
            "tags": [
                {"name": "Стресс", "color": "#ef4444", "category": "эмоции"},
                {"name": "", "color": "#000000", "category": "эмоции"},
            ],
            "quote": "  ок  ",
        }
    )
    service = TaggingService(RawLLMClient(response=raw))

    result = await service.tag_entry("текст", [])

    assert result.topic.name == "работа"
    assert result.topic.color == "#7C3AED"
    assert result.topic.category == Category.CAREER
    assert result.subtopic is not None
    assert result.subtopic.name == "дедлайны"
    assert [t.name for t in result.tags] == ["стресс"]
    assert result.tags[0].category == Category.EMOTIONS
    assert result.quote == "ок"


async def test_tag_entry_drops_tags_named_after_their_own_category():
    raw = json.dumps(
        {
            "topic": {"name": "работа", "color": "#60a5fa", "category": "карьера"},
            "subtopic": None,
            "tags": [
                {"name": "быт", "color": "#94a3b8", "category": "быт"},
                {"name": "уборка", "color": "#94a3b8", "category": "быт"},
            ],
        }
    )
    service = TaggingService(RawLLMClient(response=raw))

    result = await service.tag_entry("текст", [])

    assert [t.name for t in result.tags] == ["уборка"]


async def test_tag_entry_drops_subtopic_named_after_its_own_category():
    raw = json.dumps(
        {
            "topic": {"name": "работа", "color": "#60a5fa", "category": "карьера"},
            "subtopic": {"name": "финансы", "color": "#facc15", "category": "финансы"},
            "tags": [],
        }
    )
    service = TaggingService(RawLLMClient(response=raw))

    result = await service.tag_entry("текст", [])

    assert result.subtopic is None


async def test_tag_entry_falls_back_to_other_category_when_missing_or_invalid():
    raw = json.dumps({"topic": {"name": "работа", "category": "выдуманная-категория"}})
    service = TaggingService(RawLLMClient(response=raw))

    result = await service.tag_entry("текст", [])

    assert result.topic.category == Category.OTHER


async def test_tag_entry_falls_back_on_invalid_color():
    raw = json.dumps({"topic": {"name": "работа", "color": "not-a-hex"}})
    service = TaggingService(RawLLMClient(response=raw))

    result = await service.tag_entry("текст", [])

    assert result.topic.color.startswith("#")
    assert len(result.topic.color) == 7


async def test_tag_entry_falls_back_on_llm_error():
    service = TaggingService(RawLLMClient(raises=LLMError("boom")))

    result = await service.tag_entry("текст", [])

    assert result.topic.name == "не разобрано"
    assert result.tags == []


async def test_tag_entry_falls_back_on_malformed_json():
    service = TaggingService(RawLLMClient(response="not json at all"))

    result = await service.tag_entry("текст", [])

    assert result.topic.name == "не разобрано"


async def test_tag_entry_falls_back_on_schema_mismatch():
    service = TaggingService(RawLLMClient(response=json.dumps({"unexpected": "shape"})))

    result = await service.tag_entry("текст", [])

    assert result.topic.name == "не разобрано"


async def test_tag_entry_strict_raises_on_llm_error():
    service = TaggingService(RawLLMClient(raises=LLMError("boom")))

    with pytest.raises(LLMError):
        await service.tag_entry_strict("текст", [])


async def test_tag_entry_strict_raises_on_malformed_json():
    service = TaggingService(RawLLMClient(response="not json at all"))

    with pytest.raises(json.JSONDecodeError):
        await service.tag_entry_strict("текст", [])


async def test_tag_entry_strict_raises_on_schema_mismatch():
    service = TaggingService(RawLLMClient(response=json.dumps({"unexpected": "shape"})))

    with pytest.raises(ValidationError):
        await service.tag_entry_strict("текст", [])
