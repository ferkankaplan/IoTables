from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    audit_events,
    credentials,
    halls,
    staff_hall_assignments,
    staff_profiles,
    staff_role_assignments,
    staff_station_assignments,
    stations,
    users,
)
from iotables.security.context import ActorContext, StaffRole
from iotables.security.passwords import hash_password

DEFAULT_STAFF_PASSWORD = "12345678"


@dataclass(frozen=True)
class StaffProfile:
    user_id: UUID
    username: str
    display_name: str
    status: str
    roles: tuple[str, ...]
    station_ids: tuple[UUID, ...]
    hall_ids: tuple[UUID, ...]
    first_password_required: bool
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "userId": str(self.user_id),
            "username": self.username,
            "displayName": self.display_name,
            "status": self.status,
            "roles": list(self.roles),
            "stationIds": [str(station_id) for station_id in self.station_ids],
            "hallIds": [str(hall_id) for hall_id in self.hall_ids],
            "firstPasswordRequired": self.first_password_required,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class StaffList:
    items: tuple[StaffProfile, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {"items": [item.as_api_payload() for item in self.items]}


@dataclass(frozen=True)
class CreateStaffCommand:
    username: str
    display_name: str
    roles: tuple[StaffRole, ...]
    station_ids: tuple[UUID, ...] = ()
    hall_ids: tuple[UUID, ...] = ()


class StaffAccessService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_staff(self, *, tenant_id: UUID) -> StaffList:
        user_rows = (
            (
                await self.session.execute(
                    select(
                        users.c.id,
                        users.c.username,
                        users.c.first_password_change_required,
                        users.c.created_at,
                        users.c.updated_at,
                        staff_profiles.c.display_name,
                        staff_profiles.c.status,
                    )
                    .join(staff_profiles, staff_profiles.c.user_id == users.c.id)
                    .where(
                        users.c.tenant_id == tenant_id,
                        staff_profiles.c.tenant_id == tenant_id,
                    )
                    .order_by(staff_profiles.c.display_name, users.c.username)
                )
            )
            .mappings()
            .all()
        )
        user_ids = tuple(row["id"] for row in user_rows)
        roles_by_user = await self._active_roles_by_user(tenant_id=tenant_id, user_ids=user_ids)
        stations_by_user = await self._active_stations_by_user(
            tenant_id=tenant_id,
            user_ids=user_ids,
        )
        halls_by_user = await self._active_halls_by_user(tenant_id=tenant_id, user_ids=user_ids)

        return StaffList(
            items=tuple(
                StaffProfile(
                    user_id=row["id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    status=row["status"],
                    roles=tuple(sorted(roles_by_user.get(row["id"], ()))),
                    station_ids=tuple(sorted(stations_by_user.get(row["id"], ()), key=str)),
                    hall_ids=tuple(sorted(halls_by_user.get(row["id"], ()), key=str)),
                    first_password_required=row["first_password_change_required"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in user_rows
            )
        )

    async def create_staff(
        self,
        *,
        actor: ActorContext,
        command: CreateStaffCommand,
    ) -> StaffProfile:
        tenant_id = require_tenant_id(actor)
        if actor.user_id is None:
            raise not_authorized()
        normalized_username = normalize_username(command.username)
        display_name = command.display_name.strip()
        roles = tuple(dict.fromkeys(command.roles))
        station_ids = tuple(dict.fromkeys(command.station_ids))
        hall_ids = tuple(dict.fromkeys(command.hall_ids))
        if not normalized_username or not display_name or not roles:
            raise validation_failed()
        await self._validate_assignment_targets(
            tenant_id=tenant_id,
            roles=roles,
            station_ids=station_ids,
            hall_ids=hall_ids,
        )

        user_id = uuid4()
        now = utc_now()
        try:
            await self.session.execute(
                insert(users).values(
                    id=user_id,
                    tenant_id=tenant_id,
                    username=normalized_username,
                    status="active",
                    first_password_change_required=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self.session.execute(
                insert(credentials).values(
                    user_id=user_id,
                    password_hash=hash_password(DEFAULT_STAFF_PASSWORD),
                    bootstrap_credential=True,
                    changed_at=now,
                )
            )
            await self.session.execute(
                insert(staff_profiles).values(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    display_name=display_name,
                    status="active",
                    created_at=now,
                    updated_at=now,
                )
            )
            await self.session.execute(
                insert(staff_role_assignments).values(
                    [
                        {
                            "id": uuid4(),
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                            "role": role.value,
                            "status": "active",
                            "created_at": now,
                        }
                        for role in roles
                    ]
                )
            )
            if station_ids:
                await self.session.execute(
                    insert(staff_station_assignments).values(
                        [
                            {
                                "id": uuid4(),
                                "tenant_id": tenant_id,
                                "user_id": user_id,
                                "station_id": station_id,
                                "status": "active",
                                "created_at": now,
                            }
                            for station_id in station_ids
                        ]
                    )
                )
            if hall_ids:
                await self.session.execute(
                    insert(staff_hall_assignments).values(
                        [
                            {
                                "id": uuid4(),
                                "tenant_id": tenant_id,
                                "user_id": user_id,
                                "hall_id": hall_id,
                                "status": "active",
                                "created_at": now,
                            }
                            for hall_id in hall_ids
                        ]
                    )
                )
            await self._audit(
                tenant_id=tenant_id,
                actor=actor,
                target_id=user_id,
                metadata={
                    "operation": "staff.created",
                    "username": normalized_username,
                    "roles": [role.value for role in roles],
                    "stationIds": [str(station_id) for station_id in station_ids],
                    "hallIds": [str(hall_id) for hall_id in hall_ids],
                    "defaultPasswordApplied": True,
                    "firstPasswordOtpRequired": True,
                },
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_username() from exc

        return StaffProfile(
            user_id=user_id,
            username=normalized_username,
            display_name=display_name,
            status="active",
            roles=tuple(role.value for role in roles),
            station_ids=station_ids,
            hall_ids=hall_ids,
            first_password_required=True,
            created_at=now,
            updated_at=now,
        )

    async def disable_staff(
        self,
        *,
        actor: ActorContext,
        user_id: UUID,
        reason: str,
    ) -> StaffProfile:
        tenant_id = require_tenant_id(actor)
        if actor.user_id is None:
            raise not_authorized()
        if actor.user_id == user_id:
            raise self_disable_not_allowed()
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise reason_required()
        profile = await self._load_staff_profile(tenant_id=tenant_id, user_id=user_id)
        if profile is None:
            raise not_found()
        roles = set(profile.roles)
        if StaffRole.TENANT_ADMIN.value in roles:
            active_admin_count = await self._active_tenant_admin_count(tenant_id=tenant_id)
            if active_admin_count <= 1:
                raise last_admin_not_allowed()

        now = utc_now()
        await self.session.execute(
            update(users)
            .where(users.c.tenant_id == tenant_id, users.c.id == user_id)
            .values(status="disabled", updated_at=now)
        )
        await self.session.execute(
            update(staff_profiles)
            .where(
                staff_profiles.c.tenant_id == tenant_id,
                staff_profiles.c.user_id == user_id,
            )
            .values(status="disabled", updated_at=now)
        )
        for assignment_table in (
            staff_role_assignments,
            staff_station_assignments,
            staff_hall_assignments,
        ):
            await self.session.execute(
                update(assignment_table)
                .where(
                    assignment_table.c.tenant_id == tenant_id,
                    assignment_table.c.user_id == user_id,
                    assignment_table.c.status == "active",
                )
                .values(status="revoked", revoked_at=now)
            )
        await self._audit(
            tenant_id=tenant_id,
            actor=actor,
            action="user.disabled",
            target_id=user_id,
            metadata={
                "operation": "staff.disabled",
                "username": profile.username,
                "roles": sorted(roles),
                "reason": normalized_reason,
            },
            now=now,
        )
        await self.session.commit()
        disabled_profile = await self._load_staff_profile(tenant_id=tenant_id, user_id=user_id)
        if disabled_profile is None:
            raise not_found()
        return disabled_profile

    async def _validate_assignment_targets(
        self,
        *,
        tenant_id: UUID,
        roles: tuple[StaffRole, ...],
        station_ids: tuple[UUID, ...],
        hall_ids: tuple[UUID, ...],
    ) -> None:
        role_set = set(roles)
        if station_ids and StaffRole.STATION_STAFF not in role_set:
            raise validation_failed()
        if hall_ids and StaffRole.SERVICE_STAFF not in role_set:
            raise validation_failed()
        if station_ids:
            station_count = await self.session.scalar(
                select(func.count())
                .select_from(stations)
                .where(
                    stations.c.tenant_id == tenant_id,
                    stations.c.id.in_(station_ids),
                    stations.c.enabled.is_(True),
                )
            )
            if station_count != len(station_ids):
                raise assignment_target_disabled()
        if hall_ids:
            hall_count = await self.session.scalar(
                select(func.count())
                .select_from(halls)
                .where(
                    halls.c.tenant_id == tenant_id,
                    halls.c.id.in_(hall_ids),
                    halls.c.enabled.is_(True),
                )
            )
            if hall_count != len(hall_ids):
                raise assignment_target_disabled()

    async def _load_staff_profile(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
    ) -> StaffProfile | None:
        row = (
            (
                await self.session.execute(
                    select(
                        users.c.id,
                        users.c.username,
                        users.c.first_password_change_required,
                        users.c.created_at,
                        users.c.updated_at,
                        staff_profiles.c.display_name,
                        staff_profiles.c.status,
                    )
                    .join(staff_profiles, staff_profiles.c.user_id == users.c.id)
                    .where(
                        users.c.tenant_id == tenant_id,
                        users.c.id == user_id,
                        staff_profiles.c.tenant_id == tenant_id,
                    )
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        roles_by_user = await self._active_roles_by_user(tenant_id=tenant_id, user_ids=(user_id,))
        stations_by_user = await self._active_stations_by_user(
            tenant_id=tenant_id,
            user_ids=(user_id,),
        )
        halls_by_user = await self._active_halls_by_user(tenant_id=tenant_id, user_ids=(user_id,))
        return StaffProfile(
            user_id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            status=row["status"],
            roles=tuple(sorted(roles_by_user.get(row["id"], ()))),
            station_ids=tuple(sorted(stations_by_user.get(row["id"], ()), key=str)),
            hall_ids=tuple(sorted(halls_by_user.get(row["id"], ()), key=str)),
            first_password_required=row["first_password_change_required"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def _active_tenant_admin_count(self, *, tenant_id: UUID) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(staff_role_assignments)
                .join(users, users.c.id == staff_role_assignments.c.user_id)
                .join(staff_profiles, staff_profiles.c.user_id == staff_role_assignments.c.user_id)
                .where(
                    staff_role_assignments.c.tenant_id == tenant_id,
                    staff_role_assignments.c.role == StaffRole.TENANT_ADMIN.value,
                    staff_role_assignments.c.status == "active",
                    users.c.tenant_id == tenant_id,
                    users.c.status == "active",
                    staff_profiles.c.tenant_id == tenant_id,
                    staff_profiles.c.status == "active",
                )
            )
            or 0
        )

    async def _active_roles_by_user(
        self, *, tenant_id: UUID, user_ids: tuple[UUID, ...]
    ) -> dict[UUID, list[str]]:
        if not user_ids:
            return {}
        rows = (
            (
                await self.session.execute(
                    select(staff_role_assignments.c.user_id, staff_role_assignments.c.role).where(
                        staff_role_assignments.c.tenant_id == tenant_id,
                        staff_role_assignments.c.user_id.in_(user_ids),
                        staff_role_assignments.c.status == "active",
                    )
                )
            )
            .mappings()
            .all()
        )
        grouped: dict[UUID, list[str]] = {}
        for row in rows:
            grouped.setdefault(row["user_id"], []).append(row["role"])
        return grouped

    async def _active_stations_by_user(
        self, *, tenant_id: UUID, user_ids: tuple[UUID, ...]
    ) -> dict[UUID, list[UUID]]:
        if not user_ids:
            return {}
        rows = (
            (
                await self.session.execute(
                    select(
                        staff_station_assignments.c.user_id,
                        staff_station_assignments.c.station_id,
                    ).where(
                        staff_station_assignments.c.tenant_id == tenant_id,
                        staff_station_assignments.c.user_id.in_(user_ids),
                        staff_station_assignments.c.status == "active",
                    )
                )
            )
            .mappings()
            .all()
        )
        grouped: dict[UUID, list[UUID]] = {}
        for row in rows:
            grouped.setdefault(row["user_id"], []).append(row["station_id"])
        return grouped

    async def _active_halls_by_user(
        self, *, tenant_id: UUID, user_ids: tuple[UUID, ...]
    ) -> dict[UUID, list[UUID]]:
        if not user_ids:
            return {}
        rows = (
            (
                await self.session.execute(
                    select(
                        staff_hall_assignments.c.user_id,
                        staff_hall_assignments.c.hall_id,
                    ).where(
                        staff_hall_assignments.c.tenant_id == tenant_id,
                        staff_hall_assignments.c.user_id.in_(user_ids),
                        staff_hall_assignments.c.status == "active",
                    )
                )
            )
            .mappings()
            .all()
        )
        grouped: dict[UUID, list[UUID]] = {}
        for row in rows:
            grouped.setdefault(row["user_id"], []).append(row["hall_id"])
        return grouped

    async def _audit(
        self,
        *,
        tenant_id: UUID,
        actor: ActorContext,
        target_id: UUID,
        metadata: dict[str, object],
        now: datetime,
        action: str = "user.created",
    ) -> None:
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                action=action,
                target_type="staff_user",
                target_id=str(target_id),
                metadata=metadata,
                created_at=now,
            )
        )


def require_tenant_id(actor: ActorContext) -> UUID:
    if actor.tenant_id is None:
        raise ApiError(
            status_code=403,
            code="wrong_scope",
            message="This session is not bound to a tenant.",
        )
    return actor.tenant_id


def normalize_username(username: str) -> str:
    return username.strip().lower()


def utc_now() -> datetime:
    return datetime.now(UTC)


def validation_failed() -> ApiError:
    return ApiError(
        status_code=422,
        code="validation_failed",
        message="Some fields are invalid.",
    )


def duplicate_username() -> ApiError:
    return ApiError(
        status_code=409,
        code="duplicate_username",
        message="This username is already in use.",
    )


def assignment_target_disabled() -> ApiError:
    return ApiError(
        status_code=409,
        code="assignment_target_disabled",
        message="The requested staff assignment target is disabled or hidden.",
    )


def not_authorized() -> ApiError:
    return ApiError(
        status_code=403,
        code="not_authorized",
        message="You are not allowed to perform this action.",
    )


def not_found() -> ApiError:
    return ApiError(
        status_code=404,
        code="not_found_or_hidden",
        message="The requested staff user was not found.",
    )


def reason_required() -> ApiError:
    return ApiError(
        status_code=422,
        code="reason_required",
        message="A reason is required.",
    )


def self_disable_not_allowed() -> ApiError:
    return ApiError(
        status_code=409,
        code="self_disable_not_allowed",
        message="You cannot disable your own staff user.",
    )


def last_admin_not_allowed() -> ApiError:
    return ApiError(
        status_code=409,
        code="last_admin_not_allowed",
        message="The last tenant admin cannot be disabled.",
    )
