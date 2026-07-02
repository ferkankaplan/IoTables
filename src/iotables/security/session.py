import hashlib
import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from iotables.database.schema import (
    login_sessions,
    platform_role_assignments,
    staff_role_assignments,
    users,
)
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

SESSION_TOKEN_BYTES = 32


class NullSessionResolver:
    async def resolve(self, session_token: str) -> ActorContext | None:
        return None


class DatabaseSessionResolver:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def resolve(self, session_token: str) -> ActorContext | None:
        session_token_hash = hash_session_token(session_token)
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            row = (
                (
                    await session.execute(
                        select(
                            login_sessions.c.id.label("session_id"),
                            login_sessions.c.tenant_id,
                            login_sessions.c.user_id,
                            login_sessions.c.app_scope,
                            users.c.status.label("user_status"),
                        )
                        .join(users, users.c.id == login_sessions.c.user_id)
                        .where(
                            login_sessions.c.session_token_hash == session_token_hash,
                            login_sessions.c.expires_at > now,
                            login_sessions.c.revoked_at.is_(None),
                            users.c.status == "active",
                        )
                    )
                )
                .mappings()
                .first()
            )

            if row is None:
                return None

            app_scope = AppScope(row["app_scope"])
            if app_scope == AppScope.PLATFORM and not await self._has_platform_owner_role(
                session=session,
                user_id=row["user_id"],
            ):
                return None

            roles = await self._load_roles(
                session=session,
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                app_scope=app_scope,
            )
            actor_type = (
                ActorType.PLATFORM_OWNER
                if app_scope == AppScope.PLATFORM
                else ActorType.TENANT_USER
            )
            return ActorContext(
                actor_type=actor_type,
                app_scope=app_scope,
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                roles=roles,
                session_id=row["session_id"],
            )

    async def _load_roles(
        self,
        *,
        session: AsyncSession,
        user_id: object,
        tenant_id: object,
        app_scope: AppScope,
    ) -> frozenset[StaffRole]:
        if app_scope == AppScope.PLATFORM:
            return frozenset()

        rows = (
            await session.execute(
                select(staff_role_assignments.c.role).where(
                    staff_role_assignments.c.tenant_id == tenant_id,
                    staff_role_assignments.c.user_id == user_id,
                    staff_role_assignments.c.status == "active",
                )
            )
        ).scalars()
        return frozenset(StaffRole(role) for role in rows)

    async def _has_platform_owner_role(
        self,
        *,
        session: AsyncSession,
        user_id: object,
    ) -> bool:
        role_id = await session.scalar(
            select(platform_role_assignments.c.id).where(
                platform_role_assignments.c.user_id == user_id,
                platform_role_assignments.c.role == "platform_owner",
                platform_role_assignments.c.status == "active",
            )
        )
        return role_id is not None


def generate_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(session_token: str) -> str:
    return hashlib.sha256(session_token.encode("utf-8")).hexdigest()
