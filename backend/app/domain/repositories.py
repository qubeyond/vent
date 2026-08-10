from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities import Category, Entry, Tag, TagKind, User


class EntryRepository(Protocol):
    async def add(
        self,
        raw_text: str,
        source: str,
        quote: str | None,
        tag_ids_with_confidence: list[tuple[UUID, float | None]],
    ) -> Entry: ...

    async def get_by_id(self, entry_id: UUID) -> Entry | None: ...

    async def update_raw_text(self, entry_id: UUID, raw_text: str) -> Entry | None: ...

    async def set_tags(
        self, entry_id: UUID, tag_ids_with_confidence: list[tuple[UUID, float | None]]
    ) -> Entry | None: ...

    async def delete(self, entry_id: UUID) -> bool: ...

    async def count(self, date_from: datetime | None, date_to: datetime | None) -> int: ...

    async def list_(
        self,
        tag_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entry]: ...

    async def list_raw_texts(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> list[str]: ...

    async def list_quotes(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> list[str]: ...


class TagRepository(Protocol):
    async def get_or_create(
        self, canonical_name: str, kind: TagKind, color: str, category: Category
    ) -> Tag: ...

    async def list_with_counts(
        self,
        date_from: datetime | None,
        date_to: datetime | None,
        search: str | None = None,
    ) -> list[tuple[Tag, int]]: ...


class UserRepository(Protocol):
    async def get_by_username(self, username: str) -> User | None: ...
