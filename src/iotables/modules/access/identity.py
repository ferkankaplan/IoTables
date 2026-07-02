from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.config import Settings, get_settings
from iotables.database.schema import (
    audit_events,
    credentials,
    login_sessions,
    platform_role_assignments,
    totp_factors,
    users,
)
from iotables.security.context import ActorContext, ActorType, AppScope
from iotables.security.passwords import hash_password, verify_password
from iotables.security.session import generate_session_token, hash_session_token
from iotables.security.totp import (
    build_otpauth_url,
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_totp_secret,
    verify_totp_code,
)

SESSION_TTL = timedelta(hours=8)


@dataclass(frozen=True)
class BootstrapPlatformOwnerResult:
    user_id: UUID
    username: str
    created: bool


@dataclass(frozen=True)
class LoginResult:
    status: str
    actor: ActorContext | None
    session_token: str | None
    expires_at: datetime | None
    totp_setup: dict[str, str] | None = None

    def as_api_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "actor": actor_payload(self.actor) if self.actor is not None else None,
            "setupToken": None,
            "expiresAt": self.expires_at.isoformat() if self.expires_at is not None else None,
            "totpSetup": self.totp_setup,
        }


class IdentityAccessService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def create_platform_owner(
        self,
        *,
        username: str,
        password: str,
    ) -> BootstrapPlatformOwnerResult:
        normalized_username = normalize_username(username)
        if not password:
            raise ApiError(
                status_code=422,
                code="validation_failed",
                message="Some fields are invalid.",
            )

        async with self.session.begin():
            existing_owner = await self.session.scalar(
                select(platform_role_assignments.c.user_id).where(
                    platform_role_assignments.c.role == "platform_owner",
                    platform_role_assignments.c.status == "active",
                )
            )
            if existing_owner is not None:
                existing_username = await self.session.scalar(
                    select(users.c.username).where(users.c.id == existing_owner)
                )
                return BootstrapPlatformOwnerResult(
                    user_id=existing_owner,
                    username=existing_username or normalized_username,
                    created=False,
                )

            user_id = uuid4()
            now = utc_now()
            try:
                await self.session.execute(
                    insert(users).values(
                        id=user_id,
                        tenant_id=None,
                        username=normalized_username,
                        status="active",
                        first_password_change_required=False,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await self.session.execute(
                    insert(credentials).values(
                        user_id=user_id,
                        password_hash=hash_password(password),
                        bootstrap_credential=False,
                        changed_at=now,
                    )
                )
                await self.session.execute(
                    insert(platform_role_assignments).values(
                        id=uuid4(),
                        user_id=user_id,
                        role="platform_owner",
                        status="active",
                        created_at=now,
                        updated_at=now,
                    )
                )
                await self._insert_audit_event(
                    actor_user_id=user_id,
                    action="platform_owner.created",
                    target_type="user",
                    target_id=str(user_id),
                    metadata={"username": normalized_username},
                    created_at=now,
                )
            except IntegrityError as exc:
                raise ApiError(
                    status_code=409,
                    code="platform_owner_exists",
                    message="An active Platform Owner already exists.",
                ) from exc

            return BootstrapPlatformOwnerResult(
                user_id=user_id,
                username=normalized_username,
                created=True,
            )

    async def get_login_requirements(
        self, *, app_scope: AppScope, username: str
    ) -> dict[str, object]:
        if app_scope != AppScope.PLATFORM:
            return {
                "status": "password_required",
                "totpRequired": False,
                "firstPasswordRequired": False,
            }

        user_row = await self._load_platform_user(normalize_username(username))
        if user_row is None:
            return {
                "status": "password_required",
                "totpRequired": False,
                "firstPasswordRequired": False,
            }

        totp_enabled = await self._totp_enabled(user_row["id"])
        return {
            "status": "password_required",
            "totpRequired": totp_enabled,
            "firstPasswordRequired": bool(user_row["first_password_change_required"]),
        }

    async def authenticate_platform(
        self,
        *,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> LoginResult:
        normalized_username, user_row = await self._validate_platform_password(
            username=username,
            password=password,
        )

        if user_row["first_password_change_required"]:
            return LoginResult(
                status="first_password_required",
                actor=None,
                session_token=None,
                expires_at=None,
            )

        totp_row = await self._load_totp_factor(user_row["id"])
        if totp_row is None:
            secret = generate_totp_secret()
            return LoginResult(
                status="totp_enrollment_required",
                actor=None,
                session_token=None,
                expires_at=None,
                totp_setup={
                    "secret": secret,
                    "otpauthUrl": build_otpauth_url(
                        issuer=self.settings.app_name,
                        username=normalized_username,
                        secret=secret,
                    ),
                },
            )

        secret = decrypt_totp_secret(
            totp_row["secret_ciphertext"], self.settings.security_secret_key
        )
        if not totp_code:
            return LoginResult(
                status="totp_required",
                actor=None,
                session_token=None,
                expires_at=None,
            )
        if not verify_totp_code(secret, totp_code):
            raise ApiError(
                status_code=401,
                code="totp_invalid",
                message="TOTP code is invalid.",
            )

        return await self._create_platform_session(user_id=user_row["id"])

    async def enroll_platform_totp(
        self,
        *,
        username: str,
        password: str,
        secret: str,
        totp_code: str,
    ) -> LoginResult:
        _, user_row = await self._validate_platform_password(username=username, password=password)
        if not verify_totp_code(secret, totp_code):
            raise ApiError(
                status_code=401,
                code="totp_invalid",
                message="TOTP code is invalid.",
            )

        encrypted_secret = encrypt_totp_secret(secret, self.settings.security_secret_key)
        now = utc_now()
        existing_factor = await self._load_totp_factor(user_row["id"])
        if existing_factor is not None:
            raise ApiError(
                status_code=409,
                code="totp_already_enrolled",
                message="TOTP is already enrolled.",
            )

        await self.session.execute(
            insert(totp_factors).values(
                user_id=user_row["id"],
                secret_ciphertext=encrypted_secret,
                enrolled_at=now,
                enabled=True,
            )
        )
        await self._insert_audit_event(
            actor_user_id=user_row["id"],
            action="platform_owner.totp_enrolled",
            target_type="user",
            target_id=str(user_row["id"]),
            metadata={"method": "totp"},
            created_at=now,
        )

        return await self._create_platform_session(user_id=user_row["id"])

    async def logout(self, *, session_id: UUID) -> None:
        await self.session.execute(
            update(login_sessions)
            .where(login_sessions.c.id == session_id)
            .values(revoked_at=utc_now())
        )
        await self.session.commit()

    async def _validate_platform_password(
        self,
        *,
        username: str,
        password: str,
    ):
        normalized_username = normalize_username(username)
        user_row = await self._load_platform_user(normalized_username)
        if user_row is None:
            raise invalid_credentials()

        credential_row = (
            (
                await self.session.execute(
                    select(credentials).where(credentials.c.user_id == user_row["id"])
                )
            )
            .mappings()
            .first()
        )
        if credential_row is None or not verify_password(password, credential_row["password_hash"]):
            raise invalid_credentials()

        return normalized_username, user_row

    async def _create_platform_session(self, *, user_id: UUID) -> LoginResult:
        now = utc_now()
        expires_at = now + SESSION_TTL
        session_token = generate_session_token()
        session_id = uuid4()
        await self.session.execute(
            insert(login_sessions).values(
                id=session_id,
                tenant_id=None,
                user_id=user_id,
                app_scope=AppScope.PLATFORM.value,
                session_token_hash=hash_session_token(session_token),
                issued_at=now,
                expires_at=expires_at,
            )
        )
        await self.session.commit()

        actor = ActorContext(
            actor_type=ActorType.PLATFORM_OWNER,
            app_scope=AppScope.PLATFORM,
            user_id=user_id,
            tenant_id=None,
            session_id=session_id,
        )
        return LoginResult(
            status="authenticated",
            actor=actor,
            session_token=session_token,
            expires_at=expires_at,
        )

    async def _load_platform_user(self, username: str):
        return (
            (
                await self.session.execute(
                    select(users)
                    .join(
                        platform_role_assignments, platform_role_assignments.c.user_id == users.c.id
                    )
                    .where(
                        users.c.tenant_id.is_(None),
                        func.lower(users.c.username) == username,
                        users.c.status == "active",
                        platform_role_assignments.c.role == "platform_owner",
                        platform_role_assignments.c.status == "active",
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _load_totp_factor(self, user_id: UUID):
        return (
            (
                await self.session.execute(
                    select(totp_factors).where(
                        totp_factors.c.user_id == user_id,
                        totp_factors.c.enabled.is_(True),
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _totp_enabled(self, user_id: UUID) -> bool:
        enabled = await self.session.scalar(
            select(totp_factors.c.enabled).where(totp_factors.c.user_id == user_id)
        )
        return bool(enabled)

    async def _insert_audit_event(
        self,
        *,
        actor_user_id: UUID,
        action: str,
        target_type: str,
        target_id: str,
        metadata: dict[str, object],
        created_at: datetime,
    ) -> None:
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=None,
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata,
                created_at=created_at,
            )
        )


def actor_payload(actor: ActorContext) -> dict[str, object]:
    return {
        "userId": str(actor.user_id) if actor.user_id is not None else None,
        "tenantId": str(actor.tenant_id) if actor.tenant_id is not None else None,
        "appScope": actor.app_scope.value,
        "roles": sorted(role.value for role in actor.roles),
        "stationIds": [],
        "hallIds": [],
        "displayName": "Platform Owner" if actor.actor_type == ActorType.PLATFORM_OWNER else None,
    }


def invalid_credentials() -> ApiError:
    return ApiError(
        status_code=401,
        code="invalid_credentials",
        message="Invalid username or password.",
    )


def normalize_username(username: str) -> str:
    return username.strip().lower()


def utc_now() -> datetime:
    return datetime.now(UTC)
