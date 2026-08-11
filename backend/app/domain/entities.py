from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class TagKind(StrEnum):
    TOPIC = "topic"
    TAG = "tag"


class EntryStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"


class Category(StrEnum):
    HEALTH = "здоровье"
    CAREER = "карьера"
    FINANCE = "финансы"
    RELATIONSHIPS = "отношения"
    GROWTH = "саморазвитие"
    LEISURE = "отдых"
    HOME = "быт"
    EMOTIONS = "эмоции"
    OTHER = "другое"


@dataclass(frozen=True, slots=True)
class Tag:
    id: UUID
    canonical_name: str
    kind: TagKind
    color: str
    category: Category


@dataclass(frozen=True, slots=True)
class EntryTag:
    tag: Tag
    confidence: float | None


@dataclass(frozen=True, slots=True)
class Entry:
    id: UUID
    created_at: datetime
    raw_text: str
    source: str
    quote: str | None
    status: EntryStatus = EntryStatus.READY
    processing_error: str | None = None
    edited_at: datetime | None = None
    tags: list[EntryTag] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    username: str
    password_hash: str
    is_active: bool
