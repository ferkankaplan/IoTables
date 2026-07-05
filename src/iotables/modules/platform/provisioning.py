import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    audit_events,
    credentials,
    halls,
    menu_categories,
    product_services,
    product_variants,
    staff_hall_assignments,
    staff_profiles,
    staff_role_assignments,
    staff_station_assignments,
    starter_template_applications,
    stations,
    tenant_health,
    tenant_lifecycle_events,
    tenant_operational_settings,
    tenant_provisioning_idempotency,
    tenants,
    users,
    venue_tables,
)
from iotables.modules.platform.starter_templates import StarterTemplate, get_starter_template
from iotables.security.context import ActorContext
from iotables.security.passwords import hash_password

BOOTSTRAP_PASSWORD = "admin"


@dataclass(frozen=True)
class CreateTenantCommand:
    name: str
    subdomain: str
    gsm_number: str
    sector: str | None = None
    capacity: int | None = None
    address: str | None = None


@dataclass(frozen=True)
class ProvisioningResult:
    tenant_id: UUID
    status: str
    subdomain: str
    starter_template_applied: bool
    failure_summary: str | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tenantId": str(self.tenant_id),
            "status": self.status,
            "subdomain": self.subdomain,
            "starterTemplateApplied": self.starter_template_applied,
            "failureSummary": self.failure_summary,
        }


@dataclass(frozen=True)
class ProvisioningState:
    tenant_id: UUID
    tenant_status: str
    starter_application_status: str
    template_key: str | None
    template_version: int | None
    failure_summary: str | None
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tenantId": str(self.tenant_id),
            "tenantStatus": self.tenant_status,
            "starterApplicationStatus": self.starter_application_status,
            "templateKey": self.template_key,
            "templateVersion": self.template_version,
            "failureSummary": self.failure_summary,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class ProvisioningRecoverySummary:
    tenant_id: UUID
    missing_required_records: tuple[str, ...]
    completed_phases: tuple[str, ...]
    failed_phase: str | None
    safe_retry_allowed: bool
    failure_summary: str | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tenantId": str(self.tenant_id),
            "missingRequiredRecords": list(self.missing_required_records),
            "completedPhases": list(self.completed_phases),
            "failedPhase": self.failed_phase,
            "safeRetryAllowed": self.safe_retry_allowed,
            "failureSummary": self.failure_summary,
        }


@dataclass(frozen=True)
class TenantHealthSummary:
    tenant_id: UUID
    name: str
    subdomain: str
    status: str
    sector: str | None
    provisioning_state: str
    last_lifecycle_event_at: datetime | None
    health_flags: tuple[str, ...]
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tenantId": str(self.tenant_id),
            "name": self.name,
            "subdomain": self.subdomain,
            "status": self.status,
            "sector": self.sector,
            "provisioningState": self.provisioning_state,
            "lastLifecycleEventAt": iso_or_none(self.last_lifecycle_event_at),
            "healthFlags": list(self.health_flags),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class TenantProfile:
    tenant_id: UUID
    name: str
    subdomain: str
    gsm_number: str
    sector: str | None
    capacity: int | None
    address: str | None
    status: str
    provisioning_state: str
    starter_template_state: str
    tenant_admin_bootstrap_state: str
    health_flags: tuple[str, ...]
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tenantId": str(self.tenant_id),
            "name": self.name,
            "subdomain": self.subdomain,
            "gsmNumber": self.gsm_number,
            "sector": self.sector,
            "capacity": self.capacity,
            "address": self.address,
            "status": self.status,
            "provisioningState": self.provisioning_state,
            "starterTemplateState": self.starter_template_state,
            "tenantAdminBootstrapState": self.tenant_admin_bootstrap_state,
            "healthFlags": list(self.health_flags),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    name: str
    subdomain: str
    status: str
    sector: str | None
    capacity: int | None
    address: str | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "tenantId": str(self.tenant_id),
            "name": self.name,
            "subdomain": self.subdomain,
            "status": self.status,
            "sector": self.sector,
            "capacity": self.capacity,
            "address": self.address,
        }


@dataclass(frozen=True)
class TenantLifecycleEvent:
    event_id: UUID
    tenant_id: UUID
    previous_status: str | None
    next_status: str
    actor_user_id: UUID | None
    reason: str
    created_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "eventId": str(self.event_id),
            "tenantId": str(self.tenant_id),
            "previousStatus": self.previous_status,
            "nextStatus": self.next_status,
            "actorUserId": str(self.actor_user_id) if self.actor_user_id else None,
            "reason": self.reason,
            "createdAt": self.created_at.isoformat(),
        }


class TenantRegistryQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve_by_subdomain(self, subdomain: str) -> TenantContext:
        row = (
            (
                await self.session.execute(
                    select(tenants).where(func.lower(tenants.c.subdomain) == subdomain.lower())
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise ApiError(
                status_code=404,
                code="not_found_or_hidden",
                message="Resource was not found.",
            )
        if row["status"] != "active":
            raise ApiError(
                status_code=503,
                code="tenant_unavailable",
                message="Tenant is unavailable.",
            )
        return TenantContext(
            tenant_id=row["id"],
            name=row["name"],
            subdomain=row["subdomain"],
            status=row["status"],
            sector=row["sector"],
            capacity=row["capacity"],
            address=row["address"],
        )

    async def list_tenants(
        self,
        *,
        status: str | None = None,
        sector: str | None = None,
        q: str | None = None,
        cursor: int = 0,
        limit: int = 50,
    ) -> tuple[list[TenantHealthSummary], int | None]:
        latest_lifecycle = (
            select(
                tenant_lifecycle_events.c.tenant_id,
                func.max(tenant_lifecycle_events.c.created_at).label("last_lifecycle_event_at"),
            )
            .group_by(tenant_lifecycle_events.c.tenant_id)
            .subquery()
        )
        query = (
            select(
                tenants,
                tenant_health.c.setup_state,
                tenant_health.c.starter_template_state,
                tenant_health.c.runtime_error_summary,
                latest_lifecycle.c.last_lifecycle_event_at,
            )
            .outerjoin(tenant_health, tenant_health.c.tenant_id == tenants.c.id)
            .outerjoin(latest_lifecycle, latest_lifecycle.c.tenant_id == tenants.c.id)
            .order_by(tenants.c.created_at.desc(), tenants.c.id)
            .offset(cursor)
            .limit(limit + 1)
        )

        filters = []
        if status is not None:
            filters.append(tenants.c.status == status)
        if sector is not None:
            filters.append(tenants.c.sector == sector)
        if q:
            pattern = f"%{q.lower()}%"
            filters.append(
                or_(
                    func.lower(tenants.c.name).like(pattern),
                    func.lower(tenants.c.subdomain).like(pattern),
                )
            )
        if filters:
            query = query.where(and_(*filters))

        rows = (await self.session.execute(query)).mappings().all()
        page_rows = rows[:limit]
        items = [self._summary_from_row(row) for row in page_rows]
        next_cursor = cursor + limit if len(rows) > limit else None
        return items, next_cursor

    async def get_tenant_profile(self, tenant_id: UUID) -> TenantProfile:
        row = (
            (
                await self.session.execute(
                    select(
                        tenants,
                        tenant_health.c.setup_state,
                        tenant_health.c.starter_template_state,
                        tenant_health.c.tenant_admin_bootstrap_state,
                        tenant_health.c.runtime_error_summary,
                    )
                    .outerjoin(tenant_health, tenant_health.c.tenant_id == tenants.c.id)
                    .where(tenants.c.id == tenant_id)
                )
            )
            .mappings()
            .first()
        )

        if row is None:
            raise ApiError(
                status_code=404,
                code="not_found_or_hidden",
                message="Resource was not found.",
            )

        return TenantProfile(
            tenant_id=row["id"],
            name=row["name"],
            subdomain=row["subdomain"],
            gsm_number=row["gsm_number"],
            sector=row["sector"],
            capacity=row["capacity"],
            address=row["address"],
            status=row["status"],
            provisioning_state=row["setup_state"] or row["status"],
            starter_template_state=row["starter_template_state"] or "unknown",
            tenant_admin_bootstrap_state=row["tenant_admin_bootstrap_state"] or "unknown",
            health_flags=health_flags(
                status=row["status"],
                runtime_error_summary=row["runtime_error_summary"],
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_lifecycle_events(
        self, *, tenant_id: UUID, cursor: int, limit: int
    ) -> tuple[list[TenantLifecycleEvent], int | None]:
        await self.get_tenant_profile(tenant_id)
        bounded_limit = min(max(limit, 1), 100)
        bounded_cursor = max(cursor, 0)
        rows = (
            (
                await self.session.execute(
                    select(tenant_lifecycle_events)
                    .where(tenant_lifecycle_events.c.tenant_id == tenant_id)
                    .order_by(tenant_lifecycle_events.c.created_at.desc())
                    .offset(bounded_cursor)
                    .limit(bounded_limit + 1)
                )
            )
            .mappings()
            .all()
        )
        page_rows = rows[:bounded_limit]
        next_cursor = bounded_cursor + bounded_limit if len(rows) > bounded_limit else None
        return (
            [
                TenantLifecycleEvent(
                    event_id=row["id"],
                    tenant_id=row["tenant_id"],
                    previous_status=row["previous_status"],
                    next_status=row["next_status"],
                    actor_user_id=row["actor_user_id"],
                    reason=row["reason"],
                    created_at=row["created_at"],
                )
                for row in page_rows
            ],
            next_cursor,
        )

    def _summary_from_row(self, row: dict[str, Any]) -> TenantHealthSummary:
        return TenantHealthSummary(
            tenant_id=row["id"],
            name=row["name"],
            subdomain=row["subdomain"],
            status=row["status"],
            sector=row["sector"],
            provisioning_state=row["setup_state"] or row["status"],
            last_lifecycle_event_at=row["last_lifecycle_event_at"],
            health_flags=health_flags(
                status=row["status"],
                runtime_error_summary=row["runtime_error_summary"],
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(frozen=True)
class TenantProfileUpdateCommand:
    fields: dict[str, Any]


class TenantRegistryMutationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.query_service = TenantRegistryQueryService(session)

    async def update_profile(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        command: TenantProfileUpdateCommand,
    ) -> TenantProfile:
        if actor.user_id is None:
            raise not_authorized()

        async with self._transaction():
            current = await self._lock_tenant(tenant_id)
            values: dict[str, Any] = {"updated_at": utc_now()}
            changed_fields: list[str] = []

            if "gsm_number" in command.fields:
                gsm_number = command.fields["gsm_number"]
                if not gsm_number:
                    raise ApiError(
                        status_code=422,
                        code="validation_failed",
                        message="Some fields are invalid.",
                    )
                if gsm_number != current["gsm_number"]:
                    values["gsm_number"] = gsm_number
                    changed_fields.append("gsmNumber")
            if "sector" in command.fields:
                sector = command.fields["sector"]
                if sector is not None:
                    self._validate_sector(sector)
                if sector != current["sector"]:
                    values["sector"] = sector
                    changed_fields.append("sector")
            if "capacity" in command.fields and command.fields["capacity"] != current["capacity"]:
                values["capacity"] = command.fields["capacity"]
                changed_fields.append("capacity")
            if "address" in command.fields and command.fields["address"] != current["address"]:
                values["address"] = command.fields["address"]
                changed_fields.append("address")

            if changed_fields:
                await self.session.execute(
                    update(tenants).where(tenants.c.id == tenant_id).values(**values)
                )
                action = (
                    "tenant.gsm_changed"
                    if changed_fields == ["gsmNumber"]
                    else "tenant.profile_updated"
                )
                await insert_audit_event(
                    session=self.session,
                    tenant_id=tenant_id,
                    actor_user_id=actor.user_id,
                    action=action,
                    target_type="tenant",
                    target_id=str(tenant_id),
                    metadata={"changedFields": changed_fields},
                    created_at=values["updated_at"],
                )

        return await self.query_service.get_tenant_profile(tenant_id)

    async def change_status(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        next_status: str,
        reason: str,
    ) -> TenantProfile:
        if actor.user_id is None:
            raise not_authorized()
        if not reason.strip():
            raise ApiError(
                status_code=422,
                code="reason_required",
                message="A reason is required for this action.",
            )

        async with self._transaction():
            current = await self._lock_tenant(tenant_id)
            previous_status = current["status"]
            if previous_status == next_status:
                return await self.query_service.get_tenant_profile(tenant_id)

            if (previous_status, next_status) not in {
                ("active", "suspended"),
                ("suspended", "active"),
                ("provisioning_failed", "active"),
            }:
                raise ApiError(
                    status_code=409,
                    code="invalid_lifecycle_transition",
                    message="The requested tenant lifecycle transition is not allowed.",
                )

            now = utc_now()
            await self.session.execute(
                update(tenants)
                .where(tenants.c.id == tenant_id)
                .values(status=next_status, updated_at=now)
            )
            await self.session.execute(
                update(tenant_health)
                .where(tenant_health.c.tenant_id == tenant_id)
                .values(lifecycle_state=next_status, updated_at=now)
            )
            await self.session.execute(
                insert(tenant_lifecycle_events).values(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    previous_status=previous_status,
                    next_status=next_status,
                    actor_user_id=actor.user_id,
                    reason=reason.strip(),
                    created_at=now,
                )
            )
            await insert_audit_event(
                session=self.session,
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                action="tenant.suspended" if next_status == "suspended" else "tenant.activated",
                target_type="tenant",
                target_id=str(tenant_id),
                reason=reason.strip(),
                metadata={"previousStatus": previous_status, "nextStatus": next_status},
                created_at=now,
            )

        return await self.query_service.get_tenant_profile(tenant_id)

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[None]:
        if self.session.in_transaction():
            async with self.session.begin_nested():
                yield
            return

        async with self.session.begin():
            yield

    async def _lock_tenant(self, tenant_id: UUID) -> dict[str, Any]:
        row = (
            (
                await self.session.execute(
                    select(tenants).where(tenants.c.id == tenant_id).with_for_update()
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise ApiError(
                status_code=404,
                code="not_found_or_hidden",
                message="Resource was not found.",
            )
        return dict(row)

    def _validate_sector(self, sector: str) -> None:
        if sector not in {"cafe"}:
            raise ApiError(
                status_code=422,
                code="validation_failed",
                message="Some fields are invalid.",
            )


class TenantProvisioningService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_state(self, tenant_id: UUID) -> ProvisioningState:
        tenant_row, starter_row = await self._load_provisioning_rows(tenant_id, lock=False)
        return self._state_from_rows(tenant_row, starter_row)

    async def get_recovery_summary(self, tenant_id: UUID) -> ProvisioningRecoverySummary:
        tenant_row, starter_row = await self._load_provisioning_rows(tenant_id, lock=False)
        counts = await self._tenant_setup_counts(tenant_id)
        missing = []
        completed = []
        for phase, count in counts.items():
            if count > 0:
                completed.append(phase)
            else:
                missing.append(phase)

        starter_status = starter_row["status"] if starter_row else "not_selected"
        safe_retry_allowed = tenant_row["status"] in {
            "provisioning",
            "provisioning_failed",
        } and starter_status in {"not_selected", "failed"}
        failed_phase = None
        if tenant_row["status"] == "provisioning_failed":
            failed_phase = (
                "starter_template" if starter_status in {"failed", "recovery_needed"} else "setup"
            )
        failure_summary = (
            starter_row["failure_summary"] if starter_row else tenant_row["provisioning_error"]
        )

        return ProvisioningRecoverySummary(
            tenant_id=tenant_id,
            missing_required_records=tuple(missing),
            completed_phases=tuple(completed),
            failed_phase=failed_phase,
            safe_retry_allowed=safe_retry_allowed,
            failure_summary=failure_summary,
        )

    async def retry_failed(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        recovery_note: str | None,
    ) -> ProvisioningState:
        if actor.user_id is None:
            raise ApiError(
                status_code=403,
                code="not_authorized",
                message="You are not allowed to perform this action.",
            )

        async with self._transaction():
            tenant_row, starter_row = await self._load_provisioning_rows(tenant_id, lock=True)
            if tenant_row["status"] not in {"provisioning", "provisioning_failed"}:
                raise ApiError(
                    status_code=409,
                    code="invalid_lifecycle_transition",
                    message="The requested tenant lifecycle transition is not allowed.",
                )
            if starter_row and starter_row["status"] == "applied":
                raise ApiError(
                    status_code=409,
                    code="starter_already_applied",
                    message="Starter data has already been applied and cannot be rerun.",
                )
            if starter_row and starter_row["status"] == "recovery_needed":
                raise ApiError(
                    status_code=409,
                    code="recovery_required",
                    message="Manual recovery is required before retry.",
                )

            template = self._resolve_template(tenant_row["sector"])
            if template is not None:
                await self._apply_or_reapply_starter_template(
                    tenant_id=tenant_id,
                    template=template,
                    existing_application_id=starter_row["id"] if starter_row else None,
                    created_at=utc_now(),
                )

            now = utc_now()
            previous_status = tenant_row["status"]
            await self.session.execute(
                update(tenants)
                .where(tenants.c.id == tenant_id)
                .values(status="active", provisioning_error=None, updated_at=now)
            )
            await self.session.execute(
                update(tenant_health)
                .where(tenant_health.c.tenant_id == tenant_id)
                .values(
                    lifecycle_state="active",
                    setup_state="ready",
                    starter_template_state="applied" if template else "not_selected",
                    runtime_error_summary=None,
                    updated_at=now,
                )
            )
            await self._insert_lifecycle_event(
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                previous_status=previous_status,
                next_status="active",
                reason=(
                    recovery_note.strip()
                    if recovery_note and recovery_note.strip()
                    else "Provisioning retry completed."
                ),
                created_at=now,
            )
            await self._insert_audit_event(
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                action="tenant.activated",
                target_type="tenant",
                target_id=str(tenant_id),
                metadata={"recovery": True},
                created_at=now,
            )

        return await self.get_state(tenant_id)

    async def mark_recovery_needed(
        self,
        *,
        actor: ActorContext,
        tenant_id: UUID,
        reason: str,
    ) -> ProvisioningState:
        if actor.user_id is None:
            raise ApiError(
                status_code=403,
                code="not_authorized",
                message="You are not allowed to perform this action.",
            )
        if not reason.strip():
            raise ApiError(status_code=422, code="reason_required", message="A reason is required.")

        async with self._transaction():
            tenant_row, starter_row = await self._load_provisioning_rows(tenant_id, lock=True)
            if tenant_row["status"] not in {"provisioning", "provisioning_failed"}:
                raise ApiError(
                    status_code=409,
                    code="invalid_lifecycle_transition",
                    message="The requested tenant lifecycle transition is not allowed.",
                )
            now = utc_now()
            if starter_row is not None:
                await self.session.execute(
                    update(starter_template_applications)
                    .where(starter_template_applications.c.id == starter_row["id"])
                    .values(
                        status="recovery_needed",
                        failure_summary=reason.strip(),
                        updated_at=now,
                    )
                )
            await self.session.execute(
                update(tenants)
                .where(tenants.c.id == tenant_id)
                .values(
                    status="provisioning_failed",
                    provisioning_error=reason.strip(),
                    updated_at=now,
                )
            )
            await self.session.execute(
                update(tenant_health)
                .where(tenant_health.c.tenant_id == tenant_id)
                .values(
                    lifecycle_state="provisioning_failed",
                    setup_state="recovery_needed",
                    starter_template_state="recovery_needed" if starter_row else "not_selected",
                    runtime_error_summary=reason.strip(),
                    updated_at=now,
                )
            )

        return await self.get_state(tenant_id)

    async def start_tenant(
        self,
        *,
        actor: ActorContext,
        command: CreateTenantCommand,
        idempotency_key: str,
    ) -> ProvisioningResult:
        if actor.user_id is None:
            raise ApiError(
                status_code=403,
                code="not_authorized",
                message="You are not allowed to perform this action.",
            )

        template = self._resolve_template(command.sector)
        request_hash = self._hash_request(command)

        try:
            async with self._transaction():
                existing_payload = await self._reserve_idempotency(
                    actor_user_id=actor.user_id,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                )
                if existing_payload is not None:
                    return self._result_from_payload(existing_payload)

                result = await self._create_tenant_records(
                    actor=actor,
                    command=command,
                    template=template,
                )
                await self._complete_idempotency(
                    actor_user_id=actor.user_id,
                    idempotency_key=idempotency_key,
                    tenant_id=result.tenant_id,
                    response_payload=result.as_api_payload(),
                )
        except IntegrityError as exc:
            constraint_name = self._constraint_name(exc)
            if constraint_name == "uq_tenants__subdomain_lower":
                raise ApiError(
                    status_code=409,
                    code="duplicate_subdomain",
                    message="A tenant with this subdomain already exists.",
                ) from exc
            if constraint_name == "uq_tenant_provisioning_idempotency__actor_key":
                raise ApiError(
                    status_code=409,
                    code="request_processing",
                    message="This request is already being processed.",
                ) from exc
            raise

        return result

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[None]:
        if self.session.in_transaction():
            async with self.session.begin_nested():
                yield
            return

        async with self.session.begin():
            yield

    async def _reserve_idempotency(
        self,
        *,
        actor_user_id: UUID,
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any] | None:
        row = (
            (
                await self.session.execute(
                    select(tenant_provisioning_idempotency)
                    .where(
                        tenant_provisioning_idempotency.c.actor_user_id == actor_user_id,
                        tenant_provisioning_idempotency.c.idempotency_key == idempotency_key,
                    )
                    .with_for_update()
                )
            )
            .mappings()
            .first()
        )

        if row is None:
            await self.session.execute(
                insert(tenant_provisioning_idempotency).values(
                    id=uuid4(),
                    actor_user_id=actor_user_id,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    status="processing",
                    created_at=utc_now(),
                )
            )
            return None

        if row["request_hash"] != request_hash:
            raise ApiError(
                status_code=409,
                code="idempotency_conflict",
                message="This idempotency key was already used with a different request.",
            )

        if row["status"] == "completed":
            return row["response_payload"]

        raise ApiError(
            status_code=409,
            code="request_processing",
            message="This request is already being processed.",
        )

    async def _complete_idempotency(
        self,
        *,
        actor_user_id: UUID,
        idempotency_key: str,
        tenant_id: UUID,
        response_payload: dict[str, Any],
    ) -> None:
        await self.session.execute(
            update(tenant_provisioning_idempotency)
            .where(
                tenant_provisioning_idempotency.c.actor_user_id == actor_user_id,
                tenant_provisioning_idempotency.c.idempotency_key == idempotency_key,
            )
            .values(
                tenant_id=tenant_id,
                response_payload=response_payload,
                status="completed",
                completed_at=utc_now(),
            )
        )

    async def _create_tenant_records(
        self,
        *,
        actor: ActorContext,
        command: CreateTenantCommand,
        template: StarterTemplate | None,
    ) -> ProvisioningResult:
        duplicate = await self.session.scalar(
            select(tenants.c.id).where(func.lower(tenants.c.subdomain) == command.subdomain)
        )
        if duplicate is not None:
            raise ApiError(
                status_code=409,
                code="duplicate_subdomain",
                message="A tenant with this subdomain already exists.",
            )

        now = utc_now()
        tenant_id = uuid4()
        await self.session.execute(
            insert(tenants).values(
                id=tenant_id,
                name=command.name,
                subdomain=command.subdomain,
                gsm_number=command.gsm_number,
                sector=command.sector,
                capacity=command.capacity,
                address=command.address,
                status="provisioning",
                created_at=now,
                updated_at=now,
            )
        )
        await self._insert_lifecycle_event(
            tenant_id=tenant_id,
            actor_user_id=actor.user_id,
            previous_status=None,
            next_status="provisioning",
            reason="Tenant provisioning started.",
            created_at=now,
        )

        admin_user_id = await self._create_bootstrap_user(
            tenant_id=tenant_id,
            username=command.subdomain,
            display_name="Tenant Admin",
            role="tenant_admin",
            created_at=now,
        )

        await self.session.execute(
            insert(tenant_operational_settings).values(
                tenant_id=tenant_id,
                public_display_name=command.name,
                service_delivery_tracking_enabled=(
                    template.service_delivery_tracking_enabled if template else False
                ),
                created_at=now,
                updated_at=now,
            )
        )

        starter_applied = False
        if template is not None:
            await self._apply_starter_template(
                tenant_id=tenant_id,
                template=template,
                created_at=now,
            )
            starter_applied = True

        await self.session.execute(
            update(tenants)
            .where(tenants.c.id == tenant_id)
            .values(
                status="active",
                updated_at=now,
            )
        )
        await self.session.execute(
            insert(tenant_health).values(
                tenant_id=tenant_id,
                lifecycle_state="active",
                setup_state="ready",
                starter_template_state="applied" if starter_applied else "not_selected",
                tenant_admin_bootstrap_state="first_password_required",
                updated_at=now,
            )
        )
        await self._insert_lifecycle_event(
            tenant_id=tenant_id,
            actor_user_id=actor.user_id,
            previous_status="provisioning",
            next_status="active",
            reason="Tenant provisioning completed.",
            created_at=now,
        )
        await self._insert_audit_event(
            tenant_id=tenant_id,
            actor_user_id=actor.user_id,
            action="tenant.created",
            target_type="tenant",
            target_id=str(tenant_id),
            metadata={"subdomain": command.subdomain, "sector": command.sector},
            created_at=now,
        )
        await self._insert_audit_event(
            tenant_id=tenant_id,
            actor_user_id=actor.user_id,
            action="user.created",
            target_type="user",
            target_id=str(admin_user_id),
            metadata={"username": command.subdomain, "role": "tenant_admin"},
            created_at=now,
        )
        if starter_applied:
            await self._insert_audit_event(
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                action="starter_template.applied",
                target_type="starter_template_application",
                target_id=f"{template.template_key}:{template.template_version}",
                metadata={"sector": template.sector},
                created_at=now,
            )
        await self._insert_audit_event(
            tenant_id=tenant_id,
            actor_user_id=actor.user_id,
            action="tenant.activated",
            target_type="tenant",
            target_id=str(tenant_id),
            metadata={},
            created_at=now,
        )

        return ProvisioningResult(
            tenant_id=tenant_id,
            status="active",
            subdomain=command.subdomain,
            starter_template_applied=starter_applied,
            failure_summary=None,
        )

    async def _apply_starter_template(
        self,
        *,
        tenant_id: UUID,
        template: StarterTemplate,
        created_at: datetime,
        existing_application_id: UUID | None = None,
    ) -> None:
        if existing_application_id is None:
            await self.session.execute(
                insert(starter_template_applications).values(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    sector=template.sector,
                    template_key=template.template_key,
                    template_version=template.template_version,
                    status="applied",
                    applied_at=created_at,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
        else:
            await self.session.execute(
                update(starter_template_applications)
                .where(starter_template_applications.c.id == existing_application_id)
                .values(
                    status="applied",
                    failure_summary=None,
                    applied_at=created_at,
                    updated_at=created_at,
                )
            )

        hall_ids: dict[str, UUID] = {}
        for hall_order, hall_name in enumerate(template.halls, start=1):
            hall_id = uuid4()
            hall_ids[hall_name] = hall_id
            await self.session.execute(
                insert(halls).values(
                    id=hall_id,
                    tenant_id=tenant_id,
                    name=hall_name,
                    display_order=hall_order,
                    enabled=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
            for table_order, table_name in enumerate(template.tables_per_hall, start=1):
                await self.session.execute(
                    insert(venue_tables).values(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        hall_id=hall_id,
                        name=table_name,
                        display_order=table_order,
                        enabled=True,
                        created_at=created_at,
                        updated_at=created_at,
                    )
                )

        station_ids: dict[str, UUID] = {}
        for station_order, station_name in enumerate(template.stations, start=1):
            station_id = uuid4()
            station_ids[station_name] = station_id
            await self.session.execute(
                insert(stations).values(
                    id=station_id,
                    tenant_id=tenant_id,
                    name=station_name,
                    display_order=station_order,
                    enabled=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )

        category_ids: dict[str, UUID] = {}
        for category_order, category_name in enumerate(
            dict.fromkeys(product.category_name for product in template.products),
            start=1,
        ):
            category_id = uuid4()
            category_ids[category_name] = category_id
            await self.session.execute(
                insert(menu_categories).values(
                    id=category_id,
                    tenant_id=tenant_id,
                    name=category_name,
                    display_order=category_order,
                    enabled=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )

        for product_order, product in enumerate(template.products, start=1):
            product_id = uuid4()
            await self.session.execute(
                insert(product_services).values(
                    id=product_id,
                    tenant_id=tenant_id,
                    category_id=category_ids[product.category_name],
                    station_id=station_ids[product.station_name],
                    name=product.product_name,
                    enabled=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
            await self.session.execute(
                insert(product_variants).values(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    product_service_id=product_id,
                    name=product.variant_name,
                    price_minor=product.price_minor,
                    currency_code="TRY",
                    display_order=product_order,
                    is_default=True,
                    enabled=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )

        for staff in template.staff:
            user_id = await self._create_bootstrap_user(
                tenant_id=tenant_id,
                username=staff.username,
                display_name=staff.display_name,
                role=staff.role,
                created_at=created_at,
            )
            if staff.station_name is not None:
                await self.session.execute(
                    insert(staff_station_assignments).values(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        user_id=user_id,
                        station_id=station_ids[staff.station_name],
                        status="active",
                        created_at=created_at,
                    )
                )
            if staff.all_halls:
                for hall_id in hall_ids.values():
                    await self.session.execute(
                        insert(staff_hall_assignments).values(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            user_id=user_id,
                            hall_id=hall_id,
                            status="active",
                            created_at=created_at,
                        )
                    )

    async def _apply_or_reapply_starter_template(
        self,
        *,
        tenant_id: UUID,
        template: StarterTemplate,
        existing_application_id: UUID | None,
        created_at: datetime,
    ) -> None:
        if existing_application_id is not None:
            await self._apply_starter_template(
                tenant_id=tenant_id,
                template=template,
                created_at=created_at,
                existing_application_id=existing_application_id,
            )
            return

        await self._apply_starter_template(
            tenant_id=tenant_id,
            template=template,
            created_at=created_at,
        )

    async def _load_provisioning_rows(
        self, tenant_id: UUID, *, lock: bool
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        tenant_query = select(tenants).where(tenants.c.id == tenant_id)
        starter_query = (
            select(starter_template_applications)
            .where(starter_template_applications.c.tenant_id == tenant_id)
            .order_by(starter_template_applications.c.created_at.desc())
            .limit(1)
        )
        if lock:
            tenant_query = tenant_query.with_for_update()
            starter_query = starter_query.with_for_update()

        tenant_row = (await self.session.execute(tenant_query)).mappings().first()
        if tenant_row is None:
            raise ApiError(
                status_code=404,
                code="not_found_or_hidden",
                message="Resource was not found.",
            )

        starter_row = (await self.session.execute(starter_query)).mappings().first()
        return dict(tenant_row), dict(starter_row) if starter_row else None

    async def _tenant_setup_counts(self, tenant_id: UUID) -> dict[str, int]:
        return {
            "tenant_admin_user": await self._count_rows(users.c.tenant_id == tenant_id),
            "operational_settings": await self._count_rows(
                tenant_operational_settings.c.tenant_id == tenant_id
            ),
            "halls": await self._count_rows(halls.c.tenant_id == tenant_id),
            "stations": await self._count_rows(stations.c.tenant_id == tenant_id),
            "menu_products": await self._count_rows(product_services.c.tenant_id == tenant_id),
        }

    async def _count_rows(self, predicate: Any) -> int:
        table = predicate.left.table
        count = await self.session.scalar(select(func.count()).select_from(table).where(predicate))
        return int(count or 0)

    def _state_from_rows(
        self,
        tenant_row: dict[str, Any],
        starter_row: dict[str, Any] | None,
    ) -> ProvisioningState:
        return ProvisioningState(
            tenant_id=tenant_row["id"],
            tenant_status=tenant_row["status"],
            starter_application_status=starter_row["status"] if starter_row else "not_selected",
            template_key=starter_row["template_key"] if starter_row else None,
            template_version=starter_row["template_version"] if starter_row else None,
            failure_summary=(
                starter_row["failure_summary"] if starter_row else tenant_row["provisioning_error"]
            ),
            created_at=tenant_row["created_at"],
            updated_at=tenant_row["updated_at"],
        )

    async def _create_bootstrap_user(
        self,
        *,
        tenant_id: UUID,
        username: str,
        display_name: str,
        role: str,
        created_at: datetime,
    ) -> UUID:
        user_id = uuid4()
        await self.session.execute(
            insert(users).values(
                id=user_id,
                tenant_id=tenant_id,
                username=username,
                status="active",
                first_password_change_required=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        await self.session.execute(
            insert(credentials).values(
                user_id=user_id,
                password_hash=hash_password(BOOTSTRAP_PASSWORD),
                bootstrap_credential=True,
                changed_at=created_at,
            )
        )
        await self.session.execute(
            insert(staff_profiles).values(
                user_id=user_id,
                tenant_id=tenant_id,
                display_name=display_name,
                status="active",
                created_at=created_at,
                updated_at=created_at,
            )
        )
        await self.session.execute(
            insert(staff_role_assignments).values(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                role=role,
                status="active",
                created_at=created_at,
            )
        )
        return user_id

    async def _insert_lifecycle_event(
        self,
        *,
        tenant_id: UUID,
        actor_user_id: UUID | None,
        previous_status: str | None,
        next_status: str,
        reason: str,
        created_at: datetime,
    ) -> None:
        await self.session.execute(
            insert(tenant_lifecycle_events).values(
                id=uuid4(),
                tenant_id=tenant_id,
                previous_status=previous_status,
                next_status=next_status,
                actor_user_id=actor_user_id,
                reason=reason,
                created_at=created_at,
            )
        )

    async def _insert_audit_event(
        self,
        *,
        tenant_id: UUID,
        actor_user_id: UUID | None,
        action: str,
        target_type: str,
        target_id: str,
        metadata: dict[str, Any],
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

    def _resolve_template(self, sector: str | None) -> StarterTemplate | None:
        if sector is None:
            return None

        template = get_starter_template(sector)
        if template is None:
            raise ApiError(
                status_code=400,
                code="unsupported_sector",
                message="This sector does not have a supported starter template.",
            )
        return template

    def _hash_request(self, command: CreateTenantCommand) -> str:
        payload = json.dumps(asdict(command), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _result_from_payload(self, payload: dict[str, Any]) -> ProvisioningResult:
        return ProvisioningResult(
            tenant_id=UUID(payload["tenantId"]),
            status=payload["status"],
            subdomain=payload["subdomain"],
            starter_template_applied=payload["starterTemplateApplied"],
            failure_summary=payload["failureSummary"],
        )

    def _constraint_name(self, exc: IntegrityError) -> str | None:
        orig = getattr(exc, "orig", None)
        direct_name = getattr(orig, "constraint_name", None)
        if isinstance(direct_name, str):
            return direct_name

        cause = getattr(orig, "__cause__", None)
        cause_name = getattr(cause, "constraint_name", None)
        if isinstance(cause_name, str):
            return cause_name

        message = str(exc)
        for known_name in (
            "uq_tenants__subdomain_lower",
            "uq_tenant_provisioning_idempotency__actor_key",
        ):
            if known_name in message:
                return known_name
        return None


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def health_flags(
    *,
    status: str,
    runtime_error_summary: str | None,
) -> tuple[str, ...]:
    flags: list[str] = []
    if status == "provisioning_failed":
        flags.append("provisioning_failed")
    if status == "suspended":
        flags.append("suspended")
    if runtime_error_summary:
        flags.append("runtime_health_unknown")
    return tuple(flags)


async def insert_audit_event(
    *,
    session: AsyncSession,
    tenant_id: UUID,
    actor_user_id: UUID | None,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any],
    created_at: datetime,
    reason: str | None = None,
) -> None:
    await session.execute(
        insert(audit_events).values(
            id=uuid4(),
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            metadata=metadata,
            created_at=created_at,
        )
    )


def not_authorized() -> ApiError:
    return ApiError(
        status_code=403,
        code="not_authorized",
        message="You are not allowed to perform this action.",
    )
