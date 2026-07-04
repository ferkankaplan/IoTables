import hashlib
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.session import get_database_session
from iotables.modules.fulfillment.service_delivery import (
    ServiceDeliveryMutationService,
    ServiceDeliveryQueryService,
)
from iotables.security.context import ActorContext, AppScope
from iotables.security.dependencies import require_app_scope, require_csrf_token

SERVICE_SCOPE_DEP = Depends(require_app_scope(AppScope.SERVICE))
CSRF_DEP = Depends(require_csrf_token)

router = APIRouter(prefix="/service-staff", tags=["Service Staff"])


class ServiceReadyItemResponse(BaseModel):
    order_item_id: str = Field(alias="orderItemId")
    preparation_item_id: str = Field(alias="preparationItemId")
    table_id: str = Field(alias="tableId")
    hall_id: str = Field(alias="hallId")
    table_label: str = Field(alias="tableLabel")
    item_label: str = Field(alias="itemLabel")
    quantity: int
    preparation_ready_at: str = Field(alias="preparationReadyAt")
    delivery_status: str | None = Field(alias="deliveryStatus")


class ServiceReadyItemListResponse(BaseModel):
    items: list[ServiceReadyItemResponse]


class DeliveryStateResponse(BaseModel):
    order_item_id: str = Field(alias="orderItemId")
    preparation_item_id: str = Field(alias="preparationItemId")
    status: str
    picked_up_at: str | None = Field(alias="pickedUpAt")
    delivered_at: str | None = Field(alias="deliveredAt")
    actor_display_name: str | None = Field(alias="actorDisplayName")


class BulkDeliverRequest(BaseModel):
    table_id: UUID = Field(alias="tableId")
    order_item_ids: list[UUID] = Field(alias="orderItemIds", min_length=1)


class BulkDeliveryResultResponse(BaseModel):
    table_id: str = Field(alias="tableId")
    delivered_items: list[DeliveryStateResponse] = Field(alias="deliveredItems")
    already_delivered_items: list[str] = Field(alias="alreadyDeliveredItems")
    delivered_at: str = Field(alias="deliveredAt")
    actor_display_name: str | None = Field(alias="actorDisplayName")
    duplicate: bool


def get_service_delivery_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ServiceDeliveryQueryService:
    return ServiceDeliveryQueryService(session)


def get_service_delivery_mutation_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ServiceDeliveryMutationService:
    return ServiceDeliveryMutationService(session)


@router.get("/ready-items", response_model=ServiceReadyItemListResponse)
async def list_ready_items(
    actor: Annotated[ActorContext, SERVICE_SCOPE_DEP],
    service: Annotated[ServiceDeliveryQueryService, Depends(get_service_delivery_query_service)],
    hall_id: Annotated[UUID | None, Query(alias="hallId")] = None,
    status: str | None = None,
) -> dict[str, Any]:
    return (
        await service.list_ready_items(actor=actor, hall_id=hall_id, status=status)
    ).as_api_payload()


@router.post(
    "/items/{order_item_id}/pick-up",
    response_model=DeliveryStateResponse,
    dependencies=[CSRF_DEP],
)
async def mark_picked_up(
    order_item_id: UUID,
    actor: Annotated[ActorContext, SERVICE_SCOPE_DEP],
    service: Annotated[
        ServiceDeliveryMutationService, Depends(get_service_delivery_mutation_service)
    ],
) -> dict[str, Any]:
    return (await service.mark_picked_up(actor=actor, order_item_id=order_item_id)).as_api_payload()


@router.post(
    "/items/{order_item_id}/deliver",
    response_model=DeliveryStateResponse,
    dependencies=[CSRF_DEP],
)
async def mark_delivered(
    order_item_id: UUID,
    actor: Annotated[ActorContext, SERVICE_SCOPE_DEP],
    service: Annotated[
        ServiceDeliveryMutationService, Depends(get_service_delivery_mutation_service)
    ],
) -> dict[str, Any]:
    return (await service.mark_delivered(actor=actor, order_item_id=order_item_id)).as_api_payload()


@router.post(
    "/items/bulk-deliver",
    response_model=BulkDeliveryResultResponse,
    dependencies=[CSRF_DEP],
)
async def bulk_mark_delivered(
    payload: BulkDeliverRequest,
    actor: Annotated[ActorContext, SERVICE_SCOPE_DEP],
    service: Annotated[
        ServiceDeliveryMutationService, Depends(get_service_delivery_mutation_service)
    ],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, Any]:
    normalized_key = validate_idempotency_key(idempotency_key)
    return (
        await service.bulk_mark_delivered(
            actor=actor,
            table_id=payload.table_id,
            order_item_ids=tuple(payload.order_item_ids),
            idempotency_key=normalized_key,
            request_hash=bulk_delivery_request_hash(actor=actor, payload=payload),
        )
    ).as_api_payload()


def validate_idempotency_key(idempotency_key: str | None) -> str:
    if idempotency_key is None or not idempotency_key.strip():
        raise ApiError(
            status_code=400,
            code="idempotency_key_required",
            message="Idempotency-Key header is required.",
        )
    return idempotency_key.strip()


def bulk_delivery_request_hash(*, actor: ActorContext, payload: BulkDeliverRequest) -> str:
    normalized_payload = {
        "actorUserId": str(actor.user_id),
        "tenantId": str(actor.tenant_id),
        "tableId": str(payload.table_id),
        "orderItemIds": sorted(str(order_item_id) for order_item_id in payload.order_item_ids),
        "route": "POST /api/v1/service-staff/items/bulk-deliver",
    }
    encoded = json.dumps(normalized_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
