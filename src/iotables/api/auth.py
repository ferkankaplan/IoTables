from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.config import Settings
from iotables.database.session import get_database_session
from iotables.modules.access.identity import IdentityAccessService, actor_payload
from iotables.security.context import ActorContext, AppScope
from iotables.security.dependencies import (
    SESSION_COOKIE_NAME,
    get_current_actor,
    require_csrf_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequirementsResponse(BaseModel):
    status: str
    totp_required: bool = Field(alias="totpRequired")
    first_password_required: bool = Field(alias="firstPasswordRequired")


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    app_scope: AppScope = Field(alias="appScope")
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    totp_code: str | None = Field(default=None, alias="totpCode")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class LoginResponse(BaseModel):
    status: str
    actor: dict[str, object] | None
    setup_token: str | None = Field(alias="setupToken")
    expires_at: str | None = Field(alias="expiresAt")
    totp_setup: dict[str, str] | None = Field(alias="totpSetup")


class TotpEnrollRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    secret: str = Field(min_length=16)
    totp_code: str = Field(alias="totpCode", min_length=6, max_length=6)


class SessionResponse(BaseModel):
    actor: dict[str, object]


class LogoutResponse(BaseModel):
    status: str


def get_identity_access_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> IdentityAccessService:
    return IdentityAccessService(session, request.app.state.settings)


@router.get("/login-requirements", response_model=LoginRequirementsResponse)
async def login_requirements(
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
    app_scope: Annotated[AppScope, Query(alias="appScope")],
    username: str,
) -> dict[str, object]:
    requirements = await service.get_login_requirements(app_scope=app_scope, username=username)
    return {
        "status": requirements.get("status", "password_required"),
        "totpRequired": bool(requirements.get("totpRequired", False)),
        "firstPasswordRequired": bool(requirements.get("firstPasswordRequired", False)),
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
) -> dict[str, object]:
    if payload.app_scope != AppScope.PLATFORM:
        raise ApiError(
            status_code=403,
            code="wrong_app_scope",
            message="This session cannot access this app.",
        )

    result = await service.authenticate_platform(
        username=payload.username,
        password=payload.password,
        totp_code=payload.totp_code,
    )
    if result.session_token is not None and result.expires_at is not None:
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=result.session_token,
            httponly=True,
            secure=cookie_secure(request.app.state.settings),
            samesite="lax",
            expires=result.expires_at,
            path="/",
        )
    return result.as_api_payload()


@router.post("/totp/enroll", response_model=LoginResponse)
async def enroll_totp(
    payload: TotpEnrollRequest,
    response: Response,
    request: Request,
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
) -> dict[str, object]:
    result = await service.enroll_platform_totp(
        username=payload.username,
        password=payload.password,
        secret=payload.secret,
        totp_code=payload.totp_code,
    )
    if result.session_token is not None and result.expires_at is not None:
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=result.session_token,
            httponly=True,
            secure=cookie_secure(request.app.state.settings),
            samesite="lax",
            expires=result.expires_at,
            path="/",
        )
    return result.as_api_payload()


@router.get("/session", response_model=SessionResponse)
async def session(actor: Annotated[ActorContext, Depends(get_current_actor)]) -> dict[str, object]:
    return {"actor": actor_payload(actor)}


@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[Depends(require_csrf_token)],
)
async def logout(
    actor: Annotated[ActorContext, Depends(get_current_actor)],
    response: Response,
    request: Request,
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
) -> dict[str, str]:
    if actor.session_id is None:
        raise ApiError(
            status_code=401,
            code="unauthenticated",
            message="Authentication is required.",
        )
    await service.logout(session_id=actor.session_id)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        secure=cookie_secure(request.app.state.settings),
        samesite="lax",
        path="/",
    )
    return {"status": "logged_out"}


def cookie_secure(settings: Settings) -> bool:
    return settings.environment not in {"local", "test"}
