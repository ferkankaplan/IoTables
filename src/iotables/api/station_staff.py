from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.database.session import get_database_session
from iotables.modules.fulfillment.preparation import (
    PreparationMutationService,
    PreparationQueryService,
)
from iotables.security.context import ActorContext, AppScope
from iotables.security.dependencies import require_app_scope, require_csrf_token

STATION_SCOPE_DEP = Depends(require_app_scope(AppScope.STATION))
CSRF_DEP = Depends(require_csrf_token)

router = APIRouter(prefix="/station-staff", tags=["Station Staff"])


class PreparationQueueItemResponse(BaseModel):
    preparation_item_id: str = Field(alias="preparationItemId")
    order_item_id: str = Field(alias="orderItemId")
    station_id: str = Field(alias="stationId")
    item_label: str = Field(alias="itemLabel")
    variant_label: str = Field(alias="variantLabel")
    quantity: int
    note: str | None
    status: str
    ordered_at: str = Field(alias="orderedAt")
    updated_at: str = Field(alias="updatedAt")


class PreparationQueueResponse(BaseModel):
    items: list[PreparationQueueItemResponse]


class CannotPrepareRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=1)


def get_preparation_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> PreparationQueryService:
    return PreparationQueryService(session)


def get_preparation_mutation_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> PreparationMutationService:
    return PreparationMutationService(session)


@router.get("/queue", response_model=PreparationQueueResponse)
async def list_station_queue(
    actor: Annotated[ActorContext, STATION_SCOPE_DEP],
    service: Annotated[PreparationQueryService, Depends(get_preparation_query_service)],
    station_id: UUID,
    status: str | None = None,
) -> dict[str, Any]:
    return (
        await service.list_station_queue(actor=actor, station_id=station_id, status=status)
    ).as_api_payload()


@router.post(
    "/preparation-items/{preparation_item_id}/start",
    response_model=PreparationQueueItemResponse,
    dependencies=[CSRF_DEP],
)
async def start_preparing(
    preparation_item_id: UUID,
    actor: Annotated[ActorContext, STATION_SCOPE_DEP],
    service: Annotated[PreparationMutationService, Depends(get_preparation_mutation_service)],
) -> dict[str, Any]:
    return (
        await service.start_preparing(actor=actor, preparation_item_id=preparation_item_id)
    ).as_api_payload()


@router.post(
    "/preparation-items/{preparation_item_id}/mark-ready",
    response_model=PreparationQueueItemResponse,
    dependencies=[CSRF_DEP],
)
async def mark_ready(
    preparation_item_id: UUID,
    actor: Annotated[ActorContext, STATION_SCOPE_DEP],
    service: Annotated[PreparationMutationService, Depends(get_preparation_mutation_service)],
) -> dict[str, Any]:
    return (
        await service.mark_ready(actor=actor, preparation_item_id=preparation_item_id)
    ).as_api_payload()


@router.post(
    "/preparation-items/{preparation_item_id}/cannot-prepare",
    response_model=PreparationQueueItemResponse,
    dependencies=[CSRF_DEP],
)
async def cannot_prepare(
    preparation_item_id: UUID,
    payload: CannotPrepareRequest,
    actor: Annotated[ActorContext, STATION_SCOPE_DEP],
    service: Annotated[PreparationMutationService, Depends(get_preparation_mutation_service)],
) -> dict[str, Any]:
    return (
        await service.report_cannot_prepare(
            actor=actor,
            preparation_item_id=preparation_item_id,
            reason=payload.reason,
        )
    ).as_api_payload()
