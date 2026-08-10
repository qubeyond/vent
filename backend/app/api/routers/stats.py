from datetime import datetime

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, StatsServiceDep
from app.api.schemas.stats import QuoteCountItem, StatsSummary, TagCloudItem, WordCountItem

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
async def summary(_: CurrentUser, stats_service: StatsServiceDep) -> StatsSummary:
    total_entries, total_tags, total_chars = await stats_service.summary()
    return StatsSummary(total_entries=total_entries, total_tags=total_tags, total_chars=total_chars)


@router.get("/tag-cloud", response_model=list[TagCloudItem])
async def tag_cloud(
    _: CurrentUser,
    stats_service: StatsServiceDep,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
) -> list[TagCloudItem]:
    items = await stats_service.tag_cloud(date_from, date_to, search)
    return [
        TagCloudItem(
            id=tag.id,
            canonical_name=tag.canonical_name,
            kind=tag.kind,
            color=tag.color,
            category=tag.category,
            count=count,
        )
        for tag, count in items
    ]


@router.get("/top-words", response_model=list[WordCountItem])
async def top_words(
    _: CurrentUser,
    stats_service: StatsServiceDep,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=30, le=200),
) -> list[WordCountItem]:
    items = await stats_service.top_words(date_from, date_to, limit)
    return [WordCountItem(word=w, count=c) for w, c in items]


@router.get("/top-quotes", response_model=list[QuoteCountItem])
async def top_quotes(
    _: CurrentUser,
    stats_service: StatsServiceDep,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=10, le=100),
) -> list[QuoteCountItem]:
    items = await stats_service.top_quotes(date_from, date_to, limit)
    return [QuoteCountItem(quote=q, count=c) for q, c in items]
