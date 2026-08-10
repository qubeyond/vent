from __future__ import annotations

import structlog

from app.core.security import create_access_token, verify_password
from app.domain.repositories import UserRepository

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def login(self, username: str, password: str) -> str | None:
        user = await self._user_repo.get_by_username(username)
        if user is None or not user.is_active:
            logger.warning("login_failed", username=username, reason="no_such_user")
            return None
        if not verify_password(password, user.password_hash):
            logger.warning("login_failed", username=username, reason="wrong_password")
            return None
        return create_access_token(subject=user.username)
