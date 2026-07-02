from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.database.session import get_database_session
from iotables.modules.governance.audit import AuditQueryService
from iotables.security.context import ActorContext, AppScope
from iotables.security.dependencies import require_app_scope

PLATFORM_SCOPE_DEP = Depends(require_app_scope(AppScope.PLATFORM))

router = APIRouter(tags=["Audit"])


class AuditActorResponse(BaseModel):
    user_id: str = Field(alias="userId")


class AuditTargetResponse(BaseModel):
    type: str
    id: str


class AuditEventResponse(BaseModel):
    audit_event_id: str = Field(alias="auditEventId")
    tenant_id: str | None = Field(alias="tenantId")
    actor: AuditActorResponse | None
    action: str
    target: AuditTargetResponse
    reason: str | None
    metadata: dict[str, Any]
    created_at: str = Field(alias="createdAt")


class PageResponse(BaseModel):
    next_cursor: str | None = Field(alias="nextCursor")
    limit: int


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    page: PageResponse


def get_audit_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> AuditQueryService:
    return AuditQueryService(session)


@router.get("/platform/audit-events", response_model=AuditEventListResponse)
async def query_platform_audit_events(
    actor: Annotated[ActorContext, PLATFORM_SCOPE_DEP],
    service: Annotated[AuditQueryService, Depends(get_audit_query_service)],
    tenant_id: Annotated[UUID | None, Query(alias="tenantId")] = None,
    action: str | None = None,
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
    cursor: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    _ = actor
    bounded_limit = min(max(limit, 1), 100)
    items, next_cursor = await service.query_platform_audit(
        tenant_id=tenant_id,
        action=action,
        from_at=from_at,
        to_at=to_at,
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
