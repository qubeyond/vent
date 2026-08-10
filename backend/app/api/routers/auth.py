from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.api.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    token = await auth_service.login(body.username, body.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(user: CurrentUser) -> dict[str, str]:
    return {"username": user.username}
