from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities import Category, Entry, EntryStatus, ProcessingStage, TagKind


class EntryCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    source: str = Field(default="web", max_length=20)
    correct_text: bool = False


class EntryUpdateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    correct_text: bool = False


class TagOut(BaseModel):
    id: UUID
    canonical_name: str
    kind: TagKind
    color: str
    category: Category
    confidence: float | None = None


class EntryOut(BaseModel):
    id: UUID
    created_at: datetime
    raw_text: str
    source: str
    status: EntryStatus
    processing_stage: ProcessingStage | None
    processing_error: str | None
    quote: str | None
    edited_at: datetime | None
    tags: list[TagOut]

    @classmethod
    def from_domain(cls, entry: Entry) -> "EntryOut":
        return cls(
            id=entry.id,
            created_at=entry.created_at,
            raw_text=entry.raw_text,
            source=entry.source,
            status=entry.status,
            processing_stage=entry.processing_stage,
            processing_error=entry.processing_error,
            quote=entry.quote,
            edited_at=entry.edited_at,
            tags=[
                TagOut(
                    id=et.tag.id,
                    canonical_name=et.tag.canonical_name,
                    kind=et.tag.kind,
                    color=et.tag.color,
                    category=et.tag.category,
                    confidence=et.confidence,
                )
                for et in entry.tags
            ],
        )
