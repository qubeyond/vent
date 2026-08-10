from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.domain.entities import User
from app.infra.db.base import get_session
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
