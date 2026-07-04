from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.api.platform import TenantProfileResponse
from iotables.api.tenant_resolution import tenant_subdomain_from_request
from iotables.database.session import get_database_session
from iotables.modules.platform.provisioning import TenantRegistryQueryService
from iotables.security.context import ActorContext, AppScope, StaffRole
from iotables.security.dependencies import require_app_scope

TENANT_SCOPE_DEP = Depends(require_app_scope(AppScope.TENANT))

router = APIRouter(prefix="/tenant", tags=["Tenant"])


class TenantContextResponse(BaseModel):
    tenant_id: str = Field(alias="tenantId")
    name: str
    subdomain: str
    status: str
    sector: str | None
    capacity: int | None
    address: str | None


def get_tenant_registry_query_service_for_tenant(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TenantRegistryQueryService:
    return TenantRegistryQueryService(session)


@router.get("/context", response_model=TenantContextResponse)
async def get_tenant_context(
    request: Request,
    service: Annotated[
        TenantRegistryQueryService,
        Depends(get_tenant_registry_query_service_for_tenant),
    ],
) -> dict[str, Any]:
    subdomain = tenant_subdomain_from_request(request)
    if subdomain is None:
        raise ApiError(
            status_code=404,
            code="not_found_or_hidden",
            message="Resource was not found.",
        )
    return (await service.resolve_by_subdomain(subdomain)).as_api_payload()


@router.get("/profile", response_model=TenantProfileResponse)
async def get_own_tenant_profile(
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[
        TenantRegistryQueryService,
        Depends(get_tenant_registry_query_service_for_tenant),
    ],
) -> dict[str, Any]:
    if StaffRole.TENANT_ADMIN not in actor.roles:
        raise ApiError(
            status_code=403,
            code="not_authorized",
            message="You are not allowed to perform this action.",
        )
    if actor.tenant_id is None:
        raise ApiError(
            status_code=403,
            code="wrong_scope",
            message="This session is not bound to a tenant.",
        )
    return (await service.get_tenant_profile(actor.tenant_id)).as_api_payload()
