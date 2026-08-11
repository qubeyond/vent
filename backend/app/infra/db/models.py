import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db.base import Base

EMBEDDING_DIM = 1536


class TagModel(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("canonical_name", name="uq_tags_canonical_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="tag")
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    category: Mapped[str | None] = mapped_column(String(20), nullable=True)

    entry_links: Mapped[list["EntryTagModel"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class EntryModel(Base):
    __tablename__ = "entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ready")
    processing_stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    tag_links: Mapped[list["EntryTagModel"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", lazy="selectin"
    )


class EntryTagModel(Base):
    __tablename__ = "entry_tags"

    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    entry: Mapped[EntryModel] = relationship(back_populates="tag_links")
    tag: Mapped[TagModel] = relationship(back_populates="entry_links", lazy="joined")


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
