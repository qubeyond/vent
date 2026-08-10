import os

os.environ.setdefault("SECRET_KEY", "test-secret-at-least-32-characters-long")
os.environ.setdefault("ROUTERAI_API_KEY", "test-key")

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infra.db import models  # noqa: F401
from app.infra.db.base import Base

_DEFAULT_DEV_URL = "postgresql+asyncpg://braindump:change-me-dev@localhost:5432/braindump"
_BASE_URL = os.environ.get("DATABASE_URL", _DEFAULT_DEV_URL).rsplit("/", 1)[0]

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", f"{_BASE_URL}/braindump_test")
_TEST_DB_NAME = TEST_DATABASE_URL.rsplit("/", 1)[1]


@pytest.fixture(scope="session", autouse=True)
async def _test_database():
    admin_engine = create_async_engine(f"{_BASE_URL}/postgres", isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": _TEST_DB_NAME}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{_TEST_DB_NAME}"'))
    await admin_engine.dispose()

    schema_engine = create_async_engine(TEST_DATABASE_URL)
    async with schema_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await schema_engine.dispose()


@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.connect() as conn:
        outer = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_maker() as db_session:
            yield db_session
        await outer.rollback()
    await engine.dispose()
