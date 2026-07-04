from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.api.tenant_resolution import tenant_subdomain_from_request
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


class FirstPasswordBeginRequest(BaseModel):
    setup_token: str = Field(alias="setupToken", min_length=1)


class FirstPasswordSetupStateResponse(BaseModel):
    status: str
    setup_token: str = Field(alias="setupToken")
    otp_required: bool = Field(alias="otpRequired")
    otp_challenge_id: str | None = Field(alias="otpChallengeId")
    target_hint: str | None = Field(alias="targetHint")
    expires_at: str | None = Field(alias="expiresAt")
    remaining_attempts: int | None = Field(alias="remainingAttempts")


class FirstPasswordCompleteRequest(BaseModel):
    setup_token: str = Field(alias="setupToken", min_length=1)
    new_password: str = Field(alias="newPassword", min_length=8)
    otp_challenge_id: UUID | None = Field(default=None, alias="otpChallengeId")
    otp_code: str | None = Field(default=None, alias="otpCode", min_length=6, max_length=6)


class SessionResponse(BaseModel):
    actor: dict[str, object] | None


class LogoutResponse(BaseModel):
    status: str


def get_identity_access_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> IdentityAccessService:
    return IdentityAccessService(session, request.app.state.settings)


@router.get("/login-requirements", response_model=LoginRequirementsResponse)
async def login_requirements(
    request: Request,
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
    app_scope: Annotated[AppScope, Query(alias="appScope")],
    username: str,
) -> dict[str, object]:
    requirements = await service.get_login_requirements(
        app_scope=app_scope,
        username=username,
        tenant_subdomain=(
            tenant_subdomain_from_request(request) if app_scope != AppScope.PLATFORM else None
        ),
    )
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
    result = await service.authenticate(
        app_scope=payload.app_scope,
        username=payload.username,
        password=payload.password,
        tenant_subdomain=tenant_subdomain_from_request(request)
        if payload.app_scope != AppScope.PLATFORM
        else None,
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


@router.post("/first-password/begin", response_model=FirstPasswordSetupStateResponse)
async def begin_first_password(
    payload: FirstPasswordBeginRequest,
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
) -> dict[str, object]:
    result = await service.begin_first_password_setup(setup_token=payload.setup_token)
    return result.as_api_payload()


@router.post("/first-password/complete", response_model=LoginResponse)
async def complete_first_password(
    payload: FirstPasswordCompleteRequest,
    response: Response,
    request: Request,
    service: Annotated[IdentityAccessService, Depends(get_identity_access_service)],
) -> dict[str, object]:
    result = await service.complete_first_password_setup(
        setup_token=payload.setup_token,
        new_password=payload.new_password,
        otp_challenge_id=payload.otp_challenge_id,
        otp_code=payload.otp_code,
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
async def session(request: Request) -> dict[str, object | None]:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return {"actor": None}

    actor = await request.app.state.session_resolver.resolve(session_token)
    if actor is None:
        return {"actor": None}

    request.state.actor = actor
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
