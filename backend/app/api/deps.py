from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.domain.entities import User
from app.infra.db.base import async_session_maker, get_session
from app.infra.db.repositories import (
    SqlAlchemyEntryRepository,
    SqlAlchemyTagRepository,
    SqlAlchemyUserRepository,
)
from app.infra.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infra.llm.router_client import RouterAIClient
from app.services.auth_service import AuthService
from app.services.entry_service import EntryService
from app.services.stats_service import StatsService
from app.services.tagging_service import TaggingService
from app.services.text_correction_service import TextCorrectionService

logger = structlog.get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_db(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[AsyncSession]:
    yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_entry_service(session: DbSession, settings: SettingsDep) -> EntryService:
    llm_client = RouterAIClient(settings)
    return EntryService(
        entry_repo=SqlAlchemyEntryRepository(session),
        tag_repo=SqlAlchemyTagRepository(session),
        tagging_service=TaggingService(llm_client),
        text_correction_service=TextCorrectionService(llm_client),
        uow=SqlAlchemyUnitOfWork(session),
    )


EntryProcessor = Callable[[UUID, bool], Awaitable[None]]
IdOnlyProcessor = Callable[[UUID], Awaitable[None]]


def _build_entry_service(session: AsyncSession) -> EntryService:
    llm_client = RouterAIClient(get_settings())
    return EntryService(
        entry_repo=SqlAlchemyEntryRepository(session),
        tag_repo=SqlAlchemyTagRepository(session),
        tagging_service=TaggingService(llm_client),
        text_correction_service=TextCorrectionService(llm_client),
        uow=SqlAlchemyUnitOfWork(session),
    )


async def process_entry_in_background(entry_id: UUID, correct_text: bool) -> None:
    async with async_session_maker() as session:
        try:
            await _build_entry_service(session).process_entry(entry_id, correct_text)
        except Exception:
            logger.exception("entry_background_processing_failed", entry_id=str(entry_id))


async def process_retag_in_background(entry_id: UUID) -> None:
    async with async_session_maker() as session:
        try:
            await _build_entry_service(session).process_retag(entry_id)
        except Exception:
            logger.exception("entry_background_retag_failed", entry_id=str(entry_id))


async def process_update_correction_in_background(entry_id: UUID) -> None:
    async with async_session_maker() as session:
        try:
            await _build_entry_service(session).process_update_correction(entry_id)
        except Exception:
            logger.exception("entry_background_correction_failed", entry_id=str(entry_id))


def get_entry_processor() -> EntryProcessor:
    return process_entry_in_background


def get_retag_processor() -> IdOnlyProcessor:
    return process_retag_in_background


def get_update_correction_processor() -> IdOnlyProcessor:
    return process_update_correction_in_background


def get_stats_service(session: DbSession) -> StatsService:
    return StatsService(
        entry_repo=SqlAlchemyEntryRepository(session),
        tag_repo=SqlAlchemyTagRepository(session),
    )


def get_auth_service(session: DbSession) -> AuthService:
    return AuthService(user_repo=SqlAlchemyUserRepository(session))


async def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не авторизован",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    username = decode_access_token(credentials.credentials)
    if username is None:
        raise unauthorized
    user = await SqlAlchemyUserRepository(session).get_by_username(username)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
EntryServiceDep = Annotated[EntryService, Depends(get_entry_service)]
StatsServiceDep = Annotated[StatsService, Depends(get_stats_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
EntryProcessorDep = Annotated[EntryProcessor, Depends(get_entry_processor)]
RetagProcessorDep = Annotated[IdOnlyProcessor, Depends(get_retag_processor)]
UpdateCorrectionProcessorDep = Annotated[IdOnlyProcessor, Depends(get_update_correction_processor)]
