from uuid import UUID

from pydantic import BaseModel

from app.domain.entities import Category, TagKind


class TagCloudItem(BaseModel):
    id: UUID
    canonical_name: str
    kind: TagKind
    color: str
    category: Category
    count: int


class WordCountItem(BaseModel):
    word: str
    count: int


class QuoteCountItem(BaseModel):
    quote: str
    count: int


class StatsSummary(BaseModel):
    total_entries: int
    total_tags: int
    total_chars: int
