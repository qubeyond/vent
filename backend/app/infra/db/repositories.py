from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.color import fallback_color
from app.domain.entities import Category, Entry, EntryStatus, EntryTag, Tag, TagKind, User
from app.infra.db.models import EntryModel, EntryTagModel, TagModel, UserModel


def _category_or_fallback(value: str | None) -> Category:
    try:
        return Category(value) if value else Category.OTHER
    except ValueError:
        return Category.OTHER


def _tag_to_domain(model: TagModel) -> Tag:
    return Tag(
        id=model.id,
        canonical_name=model.canonical_name,
        kind=TagKind(model.kind),
        color=model.color or fallback_color(model.canonical_name),
        category=_category_or_fallback(model.category),
    )


def _entry_to_domain(model: EntryModel) -> Entry:
    return Entry(
        id=model.id,
        created_at=model.created_at,
        raw_text=model.raw_text,
        source=model.source,
        quote=model.quote,
        status=EntryStatus(model.status),
        processing_error=model.processing_error,
        edited_at=model.edited_at,
        tags=[
            EntryTag(tag=_tag_to_domain(link.tag), confidence=link.confidence)
            for link in model.tag_links
        ],
    )


def _user_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        username=model.username,
        password_hash=model.password_hash,
        is_active=model.is_active,
    )


class SqlAlchemyEntryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, raw_text: str, source: str, status: EntryStatus) -> Entry:
        entry = EntryModel(raw_text=raw_text, source=source, status=status.value)
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry, attribute_names=["tag_links"])
        return _entry_to_domain(entry)

    async def get_by_id(self, entry_id: UUID) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        return _entry_to_domain(model) if model is not None else None

    async def finish_processing(
        self,
        entry_id: UUID,
        raw_text: str,
        quote: str | None,
        tag_ids_with_confidence: list[tuple[UUID, float | None]],
    ) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return None
        model.raw_text = raw_text
        model.quote = quote
        model.status = EntryStatus.READY.value
        model.processing_error = None
        model.tag_links = [
            EntryTagModel(tag_id=tag_id, confidence=confidence)
            for tag_id, confidence in tag_ids_with_confidence
        ]
        await self._session.flush()
        await self._session.refresh(model, attribute_names=["tag_links"])
        for link in model.tag_links:
            await self._session.refresh(link, attribute_names=["tag"])
        return _entry_to_domain(model)

    async def mark_processing(self, entry_id: UUID) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return None
        model.status = EntryStatus.PROCESSING.value
        model.processing_error = None
        await self._session.flush()
        return _entry_to_domain(model)

    async def finish_retag(
        self, entry_id: UUID, tag_ids_with_confidence: list[tuple[UUID, float | None]]
    ) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return None
        model.status = EntryStatus.READY.value
        model.processing_error = None
        model.tag_links = [
            EntryTagModel(tag_id=tag_id, confidence=confidence)
            for tag_id, confidence in tag_ids_with_confidence
        ]
        await self._session.flush()
        await self._session.refresh(model, attribute_names=["tag_links"])
        for link in model.tag_links:
            await self._session.refresh(link, attribute_names=["tag"])
        return _entry_to_domain(model)

    async def finish_correction(self, entry_id: UUID, raw_text: str) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return None
        model.raw_text = raw_text
        model.edited_at = datetime.now(UTC)
        model.status = EntryStatus.READY.value
        model.processing_error = None
        await self._session.flush()
        return _entry_to_domain(model)

    async def mark_processing_failed(self, entry_id: UUID, error: str) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return None
        model.status = EntryStatus.READY.value
        model.processing_error = error
        await self._session.flush()
        return _entry_to_domain(model)

    async def update_raw_text(self, entry_id: UUID, raw_text: str) -> Entry | None:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return None
        model.raw_text = raw_text
        model.edited_at = datetime.now(UTC)
        await self._session.flush()
        return _entry_to_domain(model)

    async def delete(self, entry_id: UUID) -> bool:
        model = await self._session.get(EntryModel, entry_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self, date_from: datetime | None, date_to: datetime | None) -> int:
        stmt = select(func.count()).select_from(EntryModel)
        if date_from is not None:
            stmt = stmt.where(EntryModel.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(EntryModel.created_at <= date_to)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_(
        self,
        tag_ids: list[UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entry]:
        stmt = select(EntryModel).order_by(EntryModel.created_at.desc())
        if tag_ids:
            stmt = stmt.where(
                EntryModel.id.in_(
                    select(EntryTagModel.entry_id).where(EntryTagModel.tag_id.in_(tag_ids))
                )
            )
        if date_from is not None:
            stmt = stmt.where(EntryModel.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(EntryModel.created_at <= date_to)
        if search:
            stmt = stmt.where(EntryModel.raw_text.ilike(f"%{search}%"))
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_entry_to_domain(m) for m in result.scalars().unique().all()]

    async def list_raw_texts(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> list[str]:
        stmt = select(EntryModel.raw_text)
        if date_from is not None:
            stmt = stmt.where(EntryModel.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(EntryModel.created_at <= date_to)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_quotes(self, date_from: datetime | None, date_to: datetime | None) -> list[str]:
        stmt = select(EntryModel.quote).where(EntryModel.quote.is_not(None))
        if date_from is not None:
            stmt = stmt.where(EntryModel.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(EntryModel.created_at <= date_to)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SqlAlchemyTagRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_or_create(
        self, canonical_name: str, kind: TagKind, color: str, category: Category
    ) -> Tag:
        result = await self._session.execute(
            select(TagModel).where(TagModel.canonical_name == canonical_name)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return _tag_to_domain(existing)
        model = TagModel(
            canonical_name=canonical_name, kind=kind.value, color=color, category=category.value
        )
        self._session.add(model)
        await self._session.flush()
        return _tag_to_domain(model)

    async def list_with_counts(
        self,
        date_from: datetime | None,
        date_to: datetime | None,
        search: str | None = None,
    ) -> list[tuple[Tag, int]]:
        stmt = (
            select(TagModel, func.count(EntryTagModel.entry_id))
            .join(EntryTagModel, EntryTagModel.tag_id == TagModel.id)
            .join(EntryModel, EntryModel.id == EntryTagModel.entry_id)
        )
        if date_from is not None:
            stmt = stmt.where(EntryModel.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(EntryModel.created_at <= date_to)
        if search:
            stmt = stmt.where(EntryModel.raw_text.ilike(f"%{search}%"))
        stmt = stmt.group_by(TagModel.id).order_by(func.count(EntryTagModel.entry_id).desc())
        result = await self._session.execute(stmt)
        return [(_tag_to_domain(tag), count) for tag, count in result.all()]


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return _user_to_domain(model) if model else None
