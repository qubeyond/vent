from __future__ import annotations

import asyncio

import httpx

from app.core.config import Settings
from app.domain.llm_client import ChatMessage, LLMError

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 0.4


class RouterAIClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def complete(self, messages: list[ChatMessage], *, json_mode: bool = False) -> str:
        payload: dict = {
            "model": self._settings.llm_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self._settings.routerai_api_key}"}

        async with httpx.AsyncClient(
            base_url=self._settings.routerai_base_url,
            timeout=self._settings.llm_timeout_seconds,
        ) as client:
            last_error: Exception | None = None
            for attempt in range(_MAX_ATTEMPTS):
                if attempt > 0:
                    await asyncio.sleep(_BACKOFF_SECONDS * 2**attempt)
                try:
                    response = await client.post("/chat/completions", json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                except httpx.TransportError as exc:
                    last_error = exc
                    continue
                except (httpx.HTTPError, KeyError, IndexError) as exc:
                    raise LLMError(str(exc)) from exc

        raise LLMError(str(last_error))
