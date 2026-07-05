import json
import re
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.session import get_database_session
from iotables.modules.platform.provisioning import (
    CreateTenantCommand,
    TenantProfileUpdateCommand,
    TenantProvisioningService,
    TenantRegistryMutationService,
    TenantRegistryQueryService,
)
from iotables.security.context import ActorContext, AppScope
from iotables.security.dependencies import require_app_scope, require_csrf_token

SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")
PLATFORM_SCOPE_DEP = Depends(require_app_scope(AppScope.PLATFORM))
CSRF_DEP = Depends(require_csrf_token)

router = APIRouter(prefix="/platform", tags=["Platform"])


class CreateTenantRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    subdomain: str = Field(min_length=3, max_length=63)
    gsm_number: str = Field(alias="gsmNumber", min_length=5)
    sector: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    address: str | dict[str, Any] | None = None

    @field_validator("subdomain")
    @classmethod
    def normalize_subdomain(cls, value: str) -> str:
        normalized = value.lower()
        if not SUBDOMAIN_PATTERN.fullmatch(normalized):
            raise ValueError("subdomain must contain only lowercase letters, numbers, and hyphens")
        return normalized

    @field_validator("sector")
    @classmethod
    def normalize_sector(cls, value: str | None) -> str | None:
        return value.lower() if value else None

    @field_validator("address")
    @classmethod
    def serialize_address(cls, value: str | dict[str, Any] | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def to_command(self) -> CreateTenantCommand:
        return CreateTenantCommand(
            name=self.name,
            subdomain=self.subdomain,
            gsm_number=self.gsm_number,
            sector=self.sector,
            capacity=self.capacity,
            address=self.address,
        )


class ProvisioningResultResponse(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    status: str
    subdomain: str
    starter_template_applied: bool = Field(alias="starterTemplateApplied")
    failure_summary: str | None = Field(alias="failureSummary")


class ProvisioningStateResponse(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    tenant_status: str = Field(alias="tenantStatus")
    starter_application_status: str = Field(alias="starterApplicationStatus")
    template_key: str | None = Field(alias="templateKey")
    template_version: int | None = Field(alias="templateVersion")
    failure_summary: str | None = Field(alias="failureSummary")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class ProvisioningRecoverySummaryResponse(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    missing_required_records: list[str] = Field(alias="missingRequiredRecords")
    completed_phases: list[str] = Field(alias="completedPhases")
    failed_phase: str | None = Field(alias="failedPhase")
    safe_retry_allowed: bool = Field(alias="safeRetryAllowed")
    failure_summary: str | None = Field(alias="failureSummary")


class TenantHealthSummaryResponse(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    name: str
    subdomain: str
    status: str
    sector: str | None
    provisioning_state: str = Field(alias="provisioningState")
    last_lifecycle_event_at: str | None = Field(alias="lastLifecycleEventAt")
    health_flags: list[str] = Field(alias="healthFlags")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class PageResponse(BaseModel):
    next_cursor: str | None = Field(alias="nextCursor")
    limit: int


class TenantHealthListResponse(BaseModel):
    items: list[TenantHealthSummaryResponse]
    page: PageResponse


class TenantProfileResponse(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    name: str
    subdomain: str
    gsm_number: str = Field(alias="gsmNumber")
    sector: str | None
    capacity: int | None
    address: str | None
    status: str
    provisioning_state: str = Field(alias="provisioningState")
    starter_template_state: str = Field(alias="starterTemplateState")
    tenant_admin_bootstrap_state: str = Field(alias="tenantAdminBootstrapState")
    health_flags: list[str] = Field(alias="healthFlags")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class TenantLifecycleEventResponse(BaseModel):
    event_id: str = Field(alias="eventId")
    tenant_id: str = Field(alias="tenantId")
    previous_status: str | None = Field(alias="previousStatus")
    next_status: str = Field(alias="nextStatus")
    actor_user_id: str | None = Field(alias="actorUserId")
    reason: str
    created_at: str = Field(alias="createdAt")


class TenantLifecycleEventListResponse(BaseModel):
    items: list[TenantLifecycleEventResponse]
    page: PageResponse


class TenantProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    gsm_number: str | None = Field(default=None, alias="gsmNumber", min_length=5)
    sector: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    address: str | dict[str, Any] | None = None

    @field_validator("sector")
    @classmethod
    def normalize_sector(cls, value: str | None) -> str | None:
        return value.lower() if value else None

    @field_validator("address")
    @classmethod
    def serialize_address(cls, value: str | dict[str, Any] | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def to_command(self) -> TenantProfileUpdateCommand:
        fields: dict[str, Any] = {}
        if "gsm_number" in self.model_fields_set:
            fields["gsm_number"] = self.gsm_number
        if "sector" in self.model_fields_set:
            fields["sector"] = self.sector
        if "capacity" in self.model_fields_set:
            fields["capacity"] = self.capacity
        if "address" in self.model_fields_set:
            fields["address"] = self.address
        return TenantProfileUpdateCommand(fields=fields)


class TenantStatusChangeRequest(BaseModel):
    next_status: str = Field(alias="nextStatus")
    reason: str = Field(min_length=1)


class ProvisioningRetryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    recovery_note: str | None = Field(default=None, alias="recoveryNote")


class ProvisioningRecoveryNeededRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=1)


def validate_idempotency_key(idempotency_key: str | None) -> str:
    if idempotency_key is None or not idempotency_key.strip():
        raise ApiError(
            status_code=400,
            code="idempotency_key_required",
            message="Idempotency-Key header is required.",
        )

    normalized = idempotency_key.strip()
    if len(normalized) > 128:
        raise ApiError(
            status_code=422,
            code="validation_failed",
            message="Some fields are invalid.",
        )
    return normalized


def get_tenant_provisioning_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TenantProvisioningService:
    return TenantProvisioningService(session)


def get_tenant_registry_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TenantRegistryQueryService:
    return TenantRegistryQueryService(session)


def get_tenant_registry_mutation_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TenantRegistryMutationService:
    return TenantRegistryMutationService(session)


@router.get("/tenants", response_model=TenantHealthListResponse)
async def list_tenants(
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantRegistryQueryService, Depends(get_tenant_registry_query_service)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    sector: str | None = None,
    q: str | None = None,
    cursor: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    _ = actor
    bounded_limit = min(max(limit, 1), 100)
    items, next_cursor = await service.list_tenants(
        status=status_filter,
        sector=sector.lower() if sector else None,
        q=q.strip() if q else None,
        cursor=max(cursor, 0),
        limit=bounded_limit,
    )
    return {
        "items": [item.as_api_payload() for item in items],
        "page": {
            "nextCursor": str(next_cursor) if next_cursor is not None else None,
            "limit": bounded_limit,
        },
    }


@router.get("/tenants/{tenant_id}", response_model=TenantProfileResponse)
async def get_tenant(
    tenant_id: UUID,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantRegistryQueryService, Depends(get_tenant_registry_query_service)],
) -> dict[str, Any]:
    _ = actor
    return (await service.get_tenant_profile(tenant_id)).as_api_payload()


@router.get("/tenants/{tenant_id}/provisioning", response_model=ProvisioningStateResponse)
async def get_tenant_provisioning_state(
    tenant_id: UUID,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantProvisioningService, Depends(get_tenant_provisioning_service)],
) -> dict[str, Any]:
    _ = actor
    return (await service.get_state(tenant_id)).as_api_payload()


@router.get(
    "/tenants/{tenant_id}/provisioning/recovery-summary",
    response_model=ProvisioningRecoverySummaryResponse,
)
async def get_tenant_provisioning_recovery_summary(
    tenant_id: UUID,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantProvisioningService, Depends(get_tenant_provisioning_service)],
) -> dict[str, Any]:
    _ = actor
    return (await service.get_recovery_summary(tenant_id)).as_api_payload()


@router.post(
    "/tenants/{tenant_id}/provisioning/retry",
    response_model=ProvisioningStateResponse,
    dependencies=[CSRF_DEP],
)
async def retry_tenant_provisioning(
    tenant_id: UUID,
    payload: ProvisioningRetryRequest,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantProvisioningService, Depends(get_tenant_provisioning_service)],
) -> dict[str, Any]:
    return (
        await service.retry_failed(
            actor=actor,
            tenant_id=tenant_id,
            recovery_note=payload.recovery_note,
        )
    ).as_api_payload()


@router.post(
    "/tenants/{tenant_id}/provisioning/recovery-needed",
    response_model=ProvisioningStateResponse,
    dependencies=[CSRF_DEP],
)
async def mark_tenant_provisioning_recovery_needed(
    tenant_id: UUID,
    payload: ProvisioningRecoveryNeededRequest,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantProvisioningService, Depends(get_tenant_provisioning_service)],
) -> dict[str, Any]:
    return (
        await service.mark_recovery_needed(
            actor=actor,
            tenant_id=tenant_id,
            reason=payload.reason,
        )
    ).as_api_payload()


@router.get(
    "/tenants/{tenant_id}/lifecycle-events",
    response_model=TenantLifecycleEventListResponse,
)
async def list_tenant_lifecycle_events(
    tenant_id: UUID,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantRegistryQueryService, Depends(get_tenant_registry_query_service)],
    cursor: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    _ = actor
    bounded_limit = min(max(limit, 1), 100)
    items, next_cursor = await service.list_lifecycle_events(
        tenant_id=tenant_id,
        cursor=cursor,
        limit=bounded_limit,
    )
    return {
        "items": [item.as_api_payload() for item in items],
        "page": {
            "nextCursor": str(next_cursor) if next_cursor is not None else None,
            "limit": bounded_limit,
        },
    }


@router.patch(
    "/tenants/{tenant_id}/profile",
    response_model=TenantProfileResponse,
    dependencies=[CSRF_DEP],
)
async def update_tenant_profile(
    tenant_id: UUID,
    payload: TenantProfileUpdateRequest,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[
        TenantRegistryMutationService,
        Depends(get_tenant_registry_mutation_service),
    ],
) -> dict[str, Any]:
    return (
        await service.update_profile(
            actor=actor,
            tenant_id=tenant_id,
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.post(
    "/tenants/{tenant_id}/status",
    response_model=TenantProfileResponse,
    dependencies=[CSRF_DEP],
)
async def change_tenant_status(
    tenant_id: UUID,
    payload: TenantStatusChangeRequest,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[
        TenantRegistryMutationService,
        Depends(get_tenant_registry_mutation_service),
    ],
) -> dict[str, Any]:
    return (
        await service.change_status(
            actor=actor,
            tenant_id=tenant_id,
            next_status=payload.next_status,
            reason=payload.reason,
        )
    ).as_api_payload()


@router.post(
    "/tenants",
    response_model=ProvisioningResultResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CSRF_DEP],
)
async def create_tenant(
    payload: CreateTenantRequest,
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[TenantProvisioningService, Depends(get_tenant_provisioning_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    result = await service.start_tenant(
        actor=actor,
        command=payload.to_command(),
        idempotency_key=validate_idempotency_key(idempotency_key),
    )
    return result.as_api_payload()
