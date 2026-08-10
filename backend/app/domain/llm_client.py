from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


class LLMError(Exception):
    pass


class LLMClient(Protocol):
    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str: ...
