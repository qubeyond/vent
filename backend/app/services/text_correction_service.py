from __future__ import annotations

import json

import structlog
from pydantic import BaseModel, ValidationError

from app.domain.llm_client import ChatMessage, LLMClient, LLMError

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = (
    "Ты — корректор орфографии и пунктуации черновика личной заметки на "
    'русском языке. Верни ЧИСТЫЙ JSON без пояснений и markdown: {"corrected": '
    "string}.\n"
    "Правила:\n"
    "- НЕ меняй смысл, порядок мыслей, стиль, лексику. Не заменяй слова "
    "синонимами, не перефразируй, не добавляй и не убирай информацию.\n"
    "- Исправляй орфографические ошибки и опечатки в уже написанных словах — "
    "поправляй написание существующего слова, а не меняй его на другое.\n"
    "- Ставь заглавную букву в начале каждого предложения.\n"
    "- Пунктуация — по минимуму: расставляй только запятые там, где они "
    "обязательны по правилам русского языка, и точки в конце предложений. "
    "НЕ добавляй тире, двоеточия, кавычки прямой речи и другие сложные знаки "
    "препинания, если их не было в исходном тексте.\n"
    "- Если в исходном тексте уже есть сложная пунктуация (тире, двоеточия и "
    "т.п.), можно поправить её, если она расставлена неверно, но не добавляй "
    "её там, где её изначально не было.\n"
    "- Не трогай переносы строк и не объединяй/не разбивай текст на новые "
    "смысловые части.\n"
    "Ответ — только JSON, ничего больше."
)


class _CorrectionSchema(BaseModel):
    corrected: str


class TextCorrectionService:
    def __init__(self, llm_client: LLMClient):
        self._llm_client = llm_client

    async def correct(self, raw_text: str) -> str:
        messages = [
            ChatMessage(role="system", content=_SYSTEM_PROMPT),
            ChatMessage(role="user", content=raw_text),
        ]
        try:
            content = await self._llm_client.complete(messages, json_mode=True)
            parsed = _CorrectionSchema.model_validate(json.loads(content))
        except (LLMError, json.JSONDecodeError, ValidationError) as exc:
            logger.warning("text_correction_failed", error=str(exc))
            return raw_text
        corrected = parsed.corrected.strip()
        return corrected or raw_text
