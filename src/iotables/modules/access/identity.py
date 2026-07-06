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
    staff_profiles,
    staff_role_assignments,
    tenants,
    totp_factors,
    users,
)
from iotables.modules.access.otp import OtpMessagingService
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole
from iotables.security.passwords import hash_password, verify_password
from iotables.security.session import generate_session_token, hash_session_token
from iotables.security.setup_token import SetupTokenError, issue_setup_token, parse_setup_token
from iotables.security.totp import (
    encrypt_totp_secret,
    verify_totp_code,
)

SESSION_TTL = timedelta(hours=8)
FIRST_PASSWORD_SETUP_TTL = timedelta(minutes=15)
FIRST_PASSWORD_PURPOSE = "first_password"
TENANT_ADMIN_OTP_PURPOSE = "tenant_admin_first_password"
CASHIER_OTP_PURPOSE = "cashier_first_password"
APP_SCOPE_REQUIRED_ROLES = {
    AppScope.TENANT: StaffRole.TENANT_ADMIN,
    AppScope.CASHIER: StaffRole.CASHIER,
    AppScope.STATION: StaffRole.STATION_STAFF,
    AppScope.SERVICE: StaffRole.SERVICE_STAFF,
}
FIRST_PASSWORD_OTP_PURPOSES = {
    AppScope.TENANT: TENANT_ADMIN_OTP_PURPOSE,
    AppScope.CASHIER: CASHIER_OTP_PURPOSE,
}


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
    setup_token: str | None = None
    totp_setup: dict[str, str] | None = None

    def as_api_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "actor": actor_payload(self.actor) if self.actor is not None else None,
            "setupToken": self.setup_token,
            "expiresAt": self.expires_at.isoformat() if self.expires_at is not None else None,
            "totpSetup": self.totp_setup,
        }


@dataclass(frozen=True)
class FirstPasswordSetupState:
    status: str
    setup_token: str
    otp_required: bool
    otp_challenge_id: UUID | None
    target_hint: str | None
    expires_at: datetime | None
    remaining_attempts: int | None

    def as_api_payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "setupToken": self.setup_token,
            "otpRequired": self.otp_required,
            "otpChallengeId": str(self.otp_challenge_id)
            if self.otp_challenge_id is not None
            else None,
            "targetHint": self.target_hint,
            "expiresAt": self.expires_at.isoformat() if self.expires_at is not None else None,
            "remainingAttempts": self.remaining_attempts,
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
        self, *, app_scope: AppScope, username: str, tenant_subdomain: str | None = None
    ) -> dict[str, object]:
        required_role = APP_SCOPE_REQUIRED_ROLES.get(app_scope)
        if required_role is not None:
            user_row = await self._load_tenant_user(
                username=normalize_username(username),
                tenant_subdomain=tenant_subdomain,
                required_role=required_role.value,
            )
            return {
                "status": "password_required",
                "totpRequired": False,
                "firstPasswordRequired": bool(user_row["first_password_change_required"])
                if user_row
                else False,
            }

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

        return {
            "status": "password_required",
            "totpRequired": False,
            "firstPasswordRequired": bool(user_row["first_password_change_required"]),
        }

    async def authenticate(
        self,
        *,
        app_scope: AppScope,
        username: str,
        password: str,
        tenant_subdomain: str | None = None,
        totp_code: str | None = None,
    ) -> LoginResult:
        if app_scope == AppScope.PLATFORM:
            return await self.authenticate_platform(
                username=username,
                password=password,
                totp_code=totp_code,
            )
        if app_scope == AppScope.TENANT:
            return await self.authenticate_tenant_user(
                username=username,
                password=password,
                tenant_subdomain=tenant_subdomain,
                app_scope=app_scope,
                required_role=StaffRole.TENANT_ADMIN,
            )
        required_role = APP_SCOPE_REQUIRED_ROLES.get(app_scope)
        if required_role is not None:
            return await self.authenticate_tenant_user(
                username=username,
                password=password,
                tenant_subdomain=tenant_subdomain,
                app_scope=app_scope,
                required_role=required_role,
            )
        raise wrong_app_scope()

    async def authenticate_platform(
        self,
        *,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> LoginResult:
        _, user_row = await self._validate_platform_password(
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

        return await self._create_platform_session(user_id=user_row["id"])

    async def authenticate_tenant_user(
        self,
        *,
        username: str,
        password: str,
        tenant_subdomain: str | None,
        app_scope: AppScope,
        required_role: StaffRole,
    ) -> LoginResult:
        user_row = await self._load_tenant_user(
            username=normalize_username(username),
            tenant_subdomain=tenant_subdomain,
            required_role=required_role.value,
        )
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

        if user_row["first_password_change_required"]:
            return LoginResult(
                status="first_password_required",
                actor=None,
                session_token=None,
                expires_at=None,
                setup_token=self._issue_first_password_setup_token(
                    user_id=user_row["id"],
                    tenant_id=user_row["tenant_id"],
                    app_scope=app_scope,
                ),
            )

        return await self._create_tenant_session(
            user_id=user_row["id"],
            tenant_id=user_row["tenant_id"],
            app_scope=app_scope,
            role=required_role,
        )

    async def begin_first_password_setup(self, *, setup_token: str) -> FirstPasswordSetupState:
        token_payload = self._parse_first_password_setup_token(setup_token)
        app_scope = token_payload["app_scope"]
        required_role = APP_SCOPE_REQUIRED_ROLES.get(app_scope)
        if required_role is None:
            raise setup_token_invalid()

        user_row = await self._load_tenant_setup_user(
            user_id=token_payload["user_id"],
            tenant_id=token_payload["tenant_id"],
            required_role=required_role.value,
        )
        if user_row is None or not user_row["first_password_change_required"]:
            raise setup_token_invalid()
        if not user_row["bootstrap_credential"]:
            raise setup_token_invalid()

        now = utc_now()
        otp_purpose = FIRST_PASSWORD_OTP_PURPOSES.get(app_scope)
        if otp_purpose is None:
            return FirstPasswordSetupState(
                status="password_change_required",
                setup_token=setup_token,
                otp_required=False,
                otp_challenge_id=None,
                target_hint=None,
                expires_at=None,
                remaining_attempts=None,
            )

        otp = OtpMessagingService(self.session, self.settings.security_secret_key)
        challenge = await otp.create_challenge(
            tenant_id=user_row["tenant_id"],
            user_id=user_row["id"],
            purpose=otp_purpose,
            target_gsm=user_row["tenant_gsm"],
            now=now,
        )
        await self.session.commit()
        return FirstPasswordSetupState(
            status="otp_required",
            setup_token=setup_token,
            otp_required=True,
            otp_challenge_id=challenge.challenge_id,
            target_hint=challenge.target_hint,
            expires_at=challenge.expires_at,
            remaining_attempts=challenge.remaining_attempts,
        )

    async def complete_first_password_setup(
        self,
        *,
        setup_token: str,
        new_password: str,
        otp_challenge_id: UUID | None = None,
        otp_code: str | None = None,
    ) -> LoginResult:
        if len(new_password) < 8:
            raise ApiError(
                status_code=422,
                code="password_policy_failed",
                message="Password does not satisfy the policy.",
            )

        token_payload = self._parse_first_password_setup_token(setup_token)
        app_scope = token_payload["app_scope"]
        required_role = APP_SCOPE_REQUIRED_ROLES.get(app_scope)
        if required_role is None:
            raise setup_token_invalid()

        user_row = await self._load_tenant_setup_user(
            user_id=token_payload["user_id"],
            tenant_id=token_payload["tenant_id"],
            required_role=required_role.value,
        )
        if user_row is None or not user_row["first_password_change_required"]:
            raise setup_token_invalid()
        if not user_row["bootstrap_credential"]:
            raise setup_token_invalid()

        now = utc_now()
        otp_purpose = FIRST_PASSWORD_OTP_PURPOSES.get(app_scope)
        if otp_purpose is not None:
            if otp_challenge_id is None or not otp_code:
                raise ApiError(
                    status_code=403,
                    code="otp_required",
                    message="OTP proof is required.",
                )
            otp = OtpMessagingService(self.session, self.settings.security_secret_key)
            await otp.verify(
                tenant_id=user_row["tenant_id"],
                user_id=user_row["id"],
                challenge_id=otp_challenge_id,
                purpose=otp_purpose,
                code=otp_code,
                now=now,
            )
        await self.session.execute(
            update(credentials)
            .where(credentials.c.user_id == user_row["id"])
            .values(
                password_hash=hash_password(new_password),
                bootstrap_credential=False,
                changed_at=now,
            )
        )
        await self.session.execute(
            update(users)
            .where(
                users.c.id == user_row["id"],
                users.c.tenant_id == user_row["tenant_id"],
            )
            .values(first_password_change_required=False, updated_at=now)
        )
        if otp_purpose is not None and otp_challenge_id is not None:
            await self._insert_audit_event(
                tenant_id=user_row["tenant_id"],
                actor_user_id=user_row["id"],
                action="otp.verified",
                target_type="otp_challenge",
                target_id=str(otp_challenge_id),
                metadata={"purpose": otp_purpose},
                created_at=now,
            )
        await self._insert_audit_event(
            tenant_id=user_row["tenant_id"],
            actor_user_id=user_row["id"],
            action="password.changed",
            target_type="user",
            target_id=str(user_row["id"]),
            metadata={"flow": FIRST_PASSWORD_PURPOSE},
            created_at=now,
        )

        return await self._create_tenant_session(
            user_id=user_row["id"],
            tenant_id=user_row["tenant_id"],
            app_scope=app_scope,
            role=required_role,
        )

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

    async def _create_tenant_session(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        app_scope: AppScope,
        role: StaffRole,
    ) -> LoginResult:
        now = utc_now()
        expires_at = now + SESSION_TTL
        session_token = generate_session_token()
        session_id = uuid4()
        await self.session.execute(
            insert(login_sessions).values(
                id=session_id,
                tenant_id=tenant_id,
                user_id=user_id,
                app_scope=app_scope.value,
                session_token_hash=hash_session_token(session_token),
                issued_at=now,
                expires_at=expires_at,
            )
        )
        await self.session.commit()

        actor = ActorContext(
            actor_type=ActorType.TENANT_USER,
            app_scope=app_scope,
            user_id=user_id,
            tenant_id=tenant_id,
            roles=frozenset({role}),
            session_id=session_id,
        )
        return LoginResult(
            status="authenticated",
            actor=actor,
            session_token=session_token,
            expires_at=expires_at,
        )

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

    async def _load_tenant_user(
        self,
        *,
        username: str,
        tenant_subdomain: str | None,
        required_role: str,
    ):
        if tenant_subdomain is None:
            return None

        return (
            (
                await self.session.execute(
                    select(users)
                    .join(tenants, tenants.c.id == users.c.tenant_id)
                    .join(staff_profiles, staff_profiles.c.user_id == users.c.id)
                    .join(
                        staff_role_assignments,
                        staff_role_assignments.c.user_id == users.c.id,
                    )
                    .where(
                        func.lower(tenants.c.subdomain) == normalize_username(tenant_subdomain),
                        tenants.c.status == "active",
                        users.c.tenant_id == tenants.c.id,
                        func.lower(users.c.username) == username,
                        users.c.status == "active",
                        staff_profiles.c.status == "active",
                        staff_role_assignments.c.tenant_id == tenants.c.id,
                        staff_role_assignments.c.role == required_role,
                        staff_role_assignments.c.status == "active",
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _load_tenant_setup_user(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None,
        required_role: str,
    ):
        if tenant_id is None:
            return None

        return (
            (
                await self.session.execute(
                    select(
                        users.c.id,
                        users.c.tenant_id,
                        users.c.username,
                        users.c.status,
                        users.c.first_password_change_required,
                        credentials.c.bootstrap_credential,
                        tenants.c.gsm_number.label("tenant_gsm"),
                    )
                    .join(tenants, tenants.c.id == users.c.tenant_id)
                    .join(credentials, credentials.c.user_id == users.c.id)
                    .join(staff_profiles, staff_profiles.c.user_id == users.c.id)
                    .join(
                        staff_role_assignments,
                        staff_role_assignments.c.user_id == users.c.id,
                    )
                    .where(
                        users.c.id == user_id,
                        users.c.tenant_id == tenant_id,
                        users.c.status == "active",
                        tenants.c.id == tenant_id,
                        tenants.c.status == "active",
                        staff_profiles.c.tenant_id == tenant_id,
                        staff_profiles.c.status == "active",
                        staff_role_assignments.c.tenant_id == tenant_id,
                        staff_role_assignments.c.role == required_role,
                        staff_role_assignments.c.status == "active",
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
        tenant_id: UUID | None = None,
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
                tenant_id=tenant_id,
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata,
                created_at=created_at,
            )
        )

    def _issue_first_password_setup_token(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID | None,
        app_scope: AppScope,
    ) -> str:
        return issue_setup_token(
            encryption_key=self.settings.security_secret_key,
            user_id=user_id,
            tenant_id=tenant_id,
            app_scope=app_scope.value,
            purpose=FIRST_PASSWORD_PURPOSE,
            expires_at=utc_now() + FIRST_PASSWORD_SETUP_TTL,
        )

    def _parse_first_password_setup_token(self, setup_token: str) -> dict[str, object]:
        try:
            payload = parse_setup_token(
                encryption_key=self.settings.security_secret_key,
                token=setup_token,
            )
            if payload.get("purpose") != FIRST_PASSWORD_PURPOSE:
                raise SetupTokenError("wrong purpose")
            tenant_id = payload.get("tenantId")
            return {
                "user_id": UUID(str(payload["userId"])),
                "tenant_id": UUID(str(tenant_id)) if tenant_id else None,
                "app_scope": AppScope(str(payload["appScope"])),
            }
        except (SetupTokenError, ValueError, KeyError) as exc:
            raise setup_token_invalid() from exc


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


def wrong_app_scope() -> ApiError:
    return ApiError(
        status_code=403,
        code="wrong_app_scope",
        message="This session cannot access this app.",
    )


def setup_token_invalid() -> ApiError:
    return ApiError(
        status_code=410,
        code="setup_token_invalid",
        message="Setup token is invalid or expired.",
    )


def normalize_username(username: str) -> str:
    return username.strip().lower()


def utc_now() -> datetime:
    return datetime.now(UTC)
