from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class AppScope(StrEnum):
    PLATFORM = "platform"
    TENANT = "tenant"
    CASHIER = "cashier"
    STATION = "station"
    SERVICE = "service"


class ActorType(StrEnum):
    PLATFORM_OWNER = "platform_owner"
    TENANT_USER = "tenant_user"
    CUSTOMER_SESSION = "customer_session"
    DISPLAY_DEVICE = "display_device"
    SYSTEM = "system"


class StaffRole(StrEnum):
    TENANT_ADMIN = "tenant_admin"
    CASHIER = "cashier"
    STATION_STAFF = "station_staff"
    SERVICE_STAFF = "service_staff"


@dataclass(frozen=True)
class ActorContext:
    actor_type: ActorType
    app_scope: AppScope
    user_id: UUID | None = None
    tenant_id: UUID | None = None
    roles: frozenset[StaffRole] = frozenset()
    session_id: UUID | None = None

    @property
    def is_platform(self) -> bool:
        return self.actor_type == ActorType.PLATFORM_OWNER


class SessionResolver(Protocol):
    async def resolve(self, session_token: str) -> ActorContext | None:
        """Return an authenticated actor for a raw session token, or None."""
