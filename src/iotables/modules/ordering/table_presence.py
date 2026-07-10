import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    customer_ordering_sessions,
    table_access_tokens,
    table_display_credentials,
    table_sessions,
    venue_tables,
)
from iotables.security.context import ActorContext, StaffRole

TABLE_ACCESS_TOKEN_TTL = timedelta(seconds=60)
FRESH_PRESENCE_TTL = timedelta(minutes=2)
CUSTOMER_SESSION_TTL = timedelta(minutes=30)
CUSTOMER_SESSION_COOKIE_NAME = "iotables_customer_session"
CUSTOMER_SESSION_TOKEN_BYTES = 32


@dataclass(frozen=True)
class PresenceRedeemResult:
    customer_ordering_session_id: UUID
    table_id: UUID
    hall_id: UUID
    fresh_until: datetime
    session_expires_at: datetime
    customer_session_token: str
    cart_preserved: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "customerOrderingSessionId": str(self.customer_ordering_session_id),
            "tableId": str(self.table_id),
            "hallId": str(self.hall_id),
            "freshUntil": self.fresh_until.isoformat(),
            "cartPreserved": self.cart_preserved,
        }


@dataclass(frozen=True)
class PresenceState:
    customer_ordering_session_id: UUID
    table_id: UUID
    hall_id: UUID
    fresh_until: datetime
    fresh: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "customerOrderingSessionId": str(self.customer_ordering_session_id),
            "tableId": str(self.table_id),
            "hallId": str(self.hall_id),
            "freshUntil": self.fresh_until.isoformat(),
            "fresh": self.fresh,
        }


@dataclass(frozen=True)
class QrTokenPayload:
    qr_token: str
    expires_at: datetime
    refresh_after_seconds: int

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "qrToken": self.qr_token,
            "expiresAt": self.expires_at.isoformat(),
            "refreshAfterSeconds": self.refresh_after_seconds,
        }


class TablePresenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def issue_current_qr_token(self, *, display_credential: str) -> QrTokenPayload:
        now = utc_now()
        credential_row = await self._load_active_display_credential(
            display_credential=display_credential,
        )
        if credential_row is None:
            raise display_not_authenticated()
        table_row = await self._load_enabled_table(
            tenant_id=credential_row["tenant_id"],
            table_id=credential_row["table_id"],
        )
        if table_row is None:
            raise wrong_table_or_tenant()
        if table_row["mode"] != "physical":
            raise physical_display_required()

        payload = await self._issue_token_for_table(
            tenant_id=credential_row["tenant_id"],
            table_id=credential_row["table_id"],
            now=now,
        )
        await self.session.execute(
            update(table_display_credentials)
            .where(table_display_credentials.c.id == credential_row["id"])
            .values(last_seen_at=now)
        )
        await self.session.commit()
        return payload

    async def issue_virtual_table_qr_preview(
        self, *, actor: ActorContext, table_id: UUID
    ) -> QrTokenPayload:
        if StaffRole.CASHIER not in actor.roles or actor.tenant_id is None:
            raise not_authorized()
        now = utc_now()
        table_row = await self._load_enabled_table(
            tenant_id=actor.tenant_id,
            table_id=table_id,
        )
        if table_row is None:
            raise table_disabled()
        if table_row["mode"] != "virtual_test":
            raise not_virtual_test_table()
        payload = await self._issue_token_for_table(
            tenant_id=actor.tenant_id,
            table_id=table_id,
            now=now,
        )
        await self.session.commit()
        return payload

    async def redeem_token(
        self,
        *,
        tenant_id: UUID,
        raw_qr_token: str,
        existing_customer_session_token: str | None,
    ) -> PresenceRedeemResult:
        now = utc_now()
        token_row = await self._consume_token(
            raw_qr_token=raw_qr_token,
            tenant_id=tenant_id,
            now=now,
        )
        table_row = await self._load_enabled_table(
            tenant_id=tenant_id,
            table_id=token_row["table_id"],
        )
        if table_row is None:
            raise wrong_table_or_tenant()

        existing_session = None
        if existing_customer_session_token:
            existing_session = await self._load_customer_session(
                customer_session_token=existing_customer_session_token,
                now=now,
            )
            if existing_session and (
                existing_session["tenant_id"] != tenant_id
                or existing_session["table_id"] != token_row["table_id"]
            ):
                await self.session.rollback()
                raise wrong_table_or_session()

        fresh_until = now + FRESH_PRESENCE_TTL
        session_expires_at = now + CUSTOMER_SESSION_TTL
        table_session_id = await self._current_open_table_session_id(
            tenant_id=tenant_id,
            table_id=token_row["table_id"],
        )

        if existing_session is not None:
            await self.session.execute(
                update(customer_ordering_sessions)
                .where(customer_ordering_sessions.c.id == existing_session["id"])
                .values(
                    table_session_id=table_session_id,
                    presence_valid_until=fresh_until,
                    expires_at=session_expires_at,
                    last_seen_at=now,
                    updated_at=now,
                )
            )
            customer_session_token = existing_customer_session_token
            session_id = existing_session["id"]
            cart_preserved = True
        else:
            customer_session_token = generate_customer_session_token()
            session_id = uuid4()
            await self.session.execute(
                insert(customer_ordering_sessions).values(
                    id=session_id,
                    tenant_id=tenant_id,
                    table_id=token_row["table_id"],
                    table_session_id=table_session_id,
                    cookie_token_hash=hash_customer_session_token(customer_session_token),
                    presence_valid_until=fresh_until,
                    expires_at=session_expires_at,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            cart_preserved = False

        await self.session.commit()
        return PresenceRedeemResult(
            customer_ordering_session_id=session_id,
            table_id=token_row["table_id"],
            hall_id=table_row["hall_id"],
            fresh_until=fresh_until,
            session_expires_at=session_expires_at,
            customer_session_token=customer_session_token,
            cart_preserved=cart_preserved,
        )

    async def get_presence_state(
        self,
        *,
        customer_session_token: str | None,
    ) -> PresenceState:
        if not customer_session_token:
            raise session_expired()
        now = utc_now()
        session_row = await self._load_customer_session(
            customer_session_token=customer_session_token,
            now=now,
        )
        if session_row is None:
            raise session_expired()
        table_row = await self._load_enabled_table(
            tenant_id=session_row["tenant_id"],
            table_id=session_row["table_id"],
        )
        if table_row is None:
            raise fresh_presence_required()
        await self.session.execute(
            update(customer_ordering_sessions)
            .where(customer_ordering_sessions.c.id == session_row["id"])
            .values(last_seen_at=now, updated_at=now)
        )
        await self.session.commit()
        fresh = session_row["presence_valid_until"] > now
        if not fresh:
            raise fresh_presence_required()
        return PresenceState(
            customer_ordering_session_id=session_row["id"],
            table_id=session_row["table_id"],
            hall_id=table_row["hall_id"],
            fresh_until=session_row["presence_valid_until"],
            fresh=True,
        )

    async def _consume_token(self, *, raw_qr_token: str, tenant_id: UUID, now: datetime):
        token_hash = hash_table_access_token(raw_qr_token)
        result = await self.session.execute(
            update(table_access_tokens)
            .where(
                table_access_tokens.c.tenant_id == tenant_id,
                table_access_tokens.c.token_hash == token_hash,
                table_access_tokens.c.consumed_at.is_(None),
                table_access_tokens.c.expires_at > now,
            )
            .values(consumed_at=now)
            .returning(table_access_tokens)
        )
        row = result.mappings().first()
        if row is not None:
            return row

        existing = (
            (
                await self.session.execute(
                    select(table_access_tokens).where(
                        table_access_tokens.c.token_hash == token_hash,
                    )
                )
            )
            .mappings()
            .first()
        )
        await self.session.rollback()
        if existing is None or existing["expires_at"] <= now:
            raise token_expired()
        if existing["consumed_at"] is not None:
            raise token_consumed()
        raise wrong_table_or_tenant()

    async def _load_active_display_credential(self, *, display_credential: str):
        return (
            (
                await self.session.execute(
                    select(table_display_credentials).where(
                        table_display_credentials.c.credential_hash
                        == hash_display_credential(display_credential),
                        table_display_credentials.c.status == "active",
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _issue_token_for_table(
        self, *, tenant_id: UUID, table_id: UUID, now: datetime
    ) -> QrTokenPayload:
        raw_token = generate_table_access_token()
        expires_at = now + TABLE_ACCESS_TOKEN_TTL
        await self.session.execute(
            insert(table_access_tokens).values(
                id=uuid4(),
                tenant_id=tenant_id,
                table_id=table_id,
                token_hash=hash_table_access_token(raw_token),
                expires_at=expires_at,
                consumed_at=None,
                created_at=now,
            )
        )
        return QrTokenPayload(
            qr_token=raw_token,
            expires_at=expires_at,
            refresh_after_seconds=int(TABLE_ACCESS_TOKEN_TTL.total_seconds()),
        )

    async def _load_enabled_table(self, *, tenant_id: UUID, table_id: UUID):
        return (
            (
                await self.session.execute(
                    select(venue_tables).where(
                        venue_tables.c.tenant_id == tenant_id,
                        venue_tables.c.id == table_id,
                        venue_tables.c.enabled.is_(True),
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _current_open_table_session_id(
        self,
        *,
        tenant_id: UUID,
        table_id: UUID,
    ) -> UUID | None:
        row = (
            (
                await self.session.execute(
                    select(table_sessions.c.id).where(
                        table_sessions.c.tenant_id == tenant_id,
                        table_sessions.c.table_id == table_id,
                        table_sessions.c.status == "open",
                    )
                )
            )
            .mappings()
            .first()
        )
        return row["id"] if row else None

    async def _load_customer_session(self, *, customer_session_token: str, now: datetime):
        return (
            (
                await self.session.execute(
                    select(customer_ordering_sessions).where(
                        customer_ordering_sessions.c.cookie_token_hash
                        == hash_customer_session_token(customer_session_token),
                        customer_ordering_sessions.c.expires_at > now,
                    )
                )
            )
            .mappings()
            .first()
        )


def generate_customer_session_token() -> str:
    return secrets.token_urlsafe(CUSTOMER_SESSION_TOKEN_BYTES)


def generate_table_access_token() -> str:
    return secrets.token_urlsafe(CUSTOMER_SESSION_TOKEN_BYTES)


def hash_customer_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_table_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_display_credential(credential: str) -> str:
    return hashlib.sha256(credential.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


def token_expired() -> ApiError:
    return ApiError(status_code=410, code="token_expired", message="QR token expired.")


def token_consumed() -> ApiError:
    return ApiError(status_code=410, code="token_consumed", message="QR token already used.")


def wrong_table_or_tenant() -> ApiError:
    return ApiError(
        status_code=404,
        code="wrong_table_or_tenant",
        message="QR token is not valid for this tenant or table.",
    )


def wrong_table_or_session() -> ApiError:
    return ApiError(
        status_code=409,
        code="wrong_table_or_session",
        message="QR token does not match the current table session.",
    )


def session_expired() -> ApiError:
    return ApiError(status_code=401, code="session_expired", message="Session expired.")


def fresh_presence_required() -> ApiError:
    return ApiError(
        status_code=403,
        code="fresh_presence_required",
        message="Fresh table presence is required.",
    )


def display_not_authenticated() -> ApiError:
    return ApiError(
        status_code=401,
        code="display_not_authenticated",
        message="Display credential is invalid.",
    )


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def not_virtual_test_table() -> ApiError:
    return ApiError(
        status_code=409,
        code="not_virtual_test_table",
        message="QR preview is only available for virtual test tables.",
    )


def physical_display_required() -> ApiError:
    return ApiError(
        status_code=409,
        code="physical_display_required",
        message="Display QR issuance is only available for physical tables.",
    )


def table_disabled() -> ApiError:
    return ApiError(status_code=409, code="table_disabled", message="Table is disabled.")
