import json

from app.domain.llm_client import ChatMessage, LLMError
from app.services.text_correction_service import TextCorrectionService


class _StubClient:
    def __init__(self, corrected: str | None = None, raises: Exception | None = None):
        self.corrected = corrected
        self.raises = raises

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        if self.raises:
            raise self.raises
        return json.dumps({"corrected": self.corrected})


class _MalformedClient:
    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        return "not json"


async def test_correct_returns_corrected_text():
    service = TextCorrectionService(_StubClient(corrected="Привет, как дела?"))

    result = await service.correct("привет как дела")

    assert result == "Привет, как дела?"


async def test_correct_falls_back_to_original_on_llm_error():
    service = TextCorrectionService(_StubClient(raises=LLMError("роутер недоступен")))

    result = await service.correct("оригинальный текст")

    assert result == "оригинальный текст"


async def test_correct_falls_back_to_original_on_malformed_json():
    service = TextCorrectionService(_MalformedClient())

    result = await service.correct("оригинал")

    assert result == "оригинал"


async def test_correct_falls_back_when_corrected_is_blank():
    service = TextCorrectionService(_StubClient(corrected="   "))

    result = await service.correct("оригинал")

    assert result == "оригинал"
