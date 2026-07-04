from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.auth import cookie_secure
from iotables.api.errors import ApiError
from iotables.api.tenant_resolution import tenant_subdomain_from_request
from iotables.database.session import get_database_session
from iotables.modules.ordering.customer_ordering import (
    CartItemWriteCommand,
    CustomerOrderingService,
    SubmitOrderCommand,
)
from iotables.modules.ordering.table_presence import (
    CUSTOMER_SESSION_COOKIE_NAME,
    TablePresenceService,
)
from iotables.modules.platform.provisioning import TenantRegistryQueryService
from iotables.modules.tenant_setup.menu_catalog import MenuCatalogQueryService
from iotables.security.dependencies import require_csrf_token

router = APIRouter(prefix="/customer", tags=["Customer"])


class CustomerMenuVariantResponse(BaseModel):
    variant_id: str = Field(alias="variantId")
    name: str
    price_minor: int = Field(alias="priceMinor")
    currency_code: str = Field(alias="currencyCode")
    display_order: int = Field(alias="displayOrder")
    is_default: bool = Field(alias="isDefault")


class CustomerMenuOptionResponse(BaseModel):
    option_id: str = Field(alias="optionId")
    name: str
    price_delta_minor: int = Field(alias="priceDeltaMinor")
    currency_code: str = Field(alias="currencyCode")
    display_order: int = Field(alias="displayOrder")


class CustomerMenuModifierGroupResponse(BaseModel):
    group_id: str = Field(alias="groupId")
    name: str
    required: bool
    min_selections: int = Field(alias="minSelections")
    max_selections: int = Field(alias="maxSelections")
    display_order: int = Field(alias="displayOrder")
    options: list[CustomerMenuOptionResponse]


class CustomerMenuProductResponse(BaseModel):
    product_id: str = Field(alias="productId")
    category_id: str = Field(alias="categoryId")
    name: str
    description: str | None
    variants: list[CustomerMenuVariantResponse]
    modifier_groups: list[CustomerMenuModifierGroupResponse] = Field(alias="modifierGroups")


class CustomerMenuCategoryResponse(BaseModel):
    category_id: str = Field(alias="categoryId")
    name: str
    display_order: int = Field(alias="displayOrder")
    products: list[CustomerMenuProductResponse]


class CustomerMenuResponse(BaseModel):
    categories: list[CustomerMenuCategoryResponse]
    derived_at: str = Field(alias="derivedAt")


class PresenceRedeemRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    qr_token: str = Field(alias="qrToken", min_length=1)


class PresenceRedeemResponse(BaseModel):
    customer_ordering_session_id: str = Field(alias="customerOrderingSessionId")
    table_id: str = Field(alias="tableId")
    hall_id: str = Field(alias="hallId")
    fresh_until: str = Field(alias="freshUntil")
    cart_preserved: bool = Field(alias="cartPreserved")


class PresenceStateResponse(BaseModel):
    customer_ordering_session_id: str = Field(alias="customerOrderingSessionId")
    table_id: str = Field(alias="tableId")
    hall_id: str = Field(alias="hallId")
    fresh_until: str = Field(alias="freshUntil")
    fresh: bool


class CartItemResponse(BaseModel):
    client_cart_item_id: str = Field(alias="clientCartItemId")
    product_id: str = Field(alias="productId")
    variant_id: str = Field(alias="variantId")
    quantity: int
    modifier_option_ids: list[str] = Field(alias="modifierOptionIds")
    note: str | None
    estimated_price_minor: int = Field(alias="estimatedPriceMinor")


class CartResponse(BaseModel):
    cart_id: str = Field(alias="cartId")
    version: str
    items: list[CartItemResponse]
    display_subtotal_minor: int = Field(alias="displaySubtotalMinor")
    currency: str
    updated_at: str = Field(alias="updatedAt")


class CartItemWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_cart_item_id: str = Field(alias="clientCartItemId", min_length=1)
    product_id: UUID = Field(alias="productId")
    variant_id: UUID = Field(alias="variantId")
    modifier_option_ids: list[UUID] = Field(default_factory=list, alias="modifierOptionIds")
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=240)

    def to_command(self) -> CartItemWriteCommand:
        return CartItemWriteCommand(
            client_cart_item_id=self.client_cart_item_id,
            product_id=self.product_id,
            variant_id=self.variant_id,
            modifier_option_ids=tuple(self.modifier_option_ids),
            quantity=self.quantity,
            note=self.note,
        )


class SubmitOrderRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    cart_version: str = Field(alias="cartVersion", min_length=1)
    cart_item_ids: list[str] = Field(alias="cartItemIds", min_length=1)

    def to_command(self) -> SubmitOrderCommand:
        return SubmitOrderCommand(
            cart_version=self.cart_version,
            cart_item_ids=tuple(self.cart_item_ids),
        )


class SubmittedOrderItemResponse(BaseModel):
    order_item_id: str = Field(alias="orderItemId")
    product_id: str = Field(alias="productId")
    variant_id: str = Field(alias="variantId")
    station_id: str = Field(alias="stationId")
    name: str
    variant_name: str = Field(alias="variantName")
    quantity: int
    unit_price_minor: int = Field(alias="unitPriceMinor")
    note: str | None


class SubmittedOrderResultResponse(BaseModel):
    order_id: str = Field(alias="orderId")
    table_session_id: str = Field(alias="tableSessionId")
    check_id: str = Field(alias="checkId")
    items: list[SubmittedOrderItemResponse]
    cart_cleared: bool = Field(alias="cartCleared")
    duplicate: bool


def get_customer_tenant_registry_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TenantRegistryQueryService:
    return TenantRegistryQueryService(session)


def get_customer_menu_catalog_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> MenuCatalogQueryService:
    return MenuCatalogQueryService(session)


def get_table_presence_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TablePresenceService:
    return TablePresenceService(session)


def get_customer_ordering_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> CustomerOrderingService:
    return CustomerOrderingService(session)


@router.get("/menu", response_model=CustomerMenuResponse)
async def get_customer_menu(
    request: Request,
    tenant_service: Annotated[
        TenantRegistryQueryService,
        Depends(get_customer_tenant_registry_query_service),
    ],
    menu_service: Annotated[
        MenuCatalogQueryService,
        Depends(get_customer_menu_catalog_query_service),
    ],
) -> dict[str, Any]:
    subdomain = tenant_subdomain_from_request(request)
    if subdomain is None:
        raise ApiError(
            status_code=404,
            code="not_found_or_hidden",
            message="Resource was not found.",
        )
    tenant = await tenant_service.resolve_by_subdomain(subdomain)
    return (await menu_service.get_customer_menu(tenant_id=tenant.tenant_id)).as_api_payload()


@router.post("/table-presence/redeem", response_model=PresenceRedeemResponse)
async def redeem_table_presence(
    payload: PresenceRedeemRequest,
    request: Request,
    response: Response,
    tenant_service: Annotated[
        TenantRegistryQueryService,
        Depends(get_customer_tenant_registry_query_service),
    ],
    presence_service: Annotated[TablePresenceService, Depends(get_table_presence_service)],
) -> dict[str, Any]:
    subdomain = tenant_subdomain_from_request(request)
    if subdomain is None:
        raise ApiError(
            status_code=404,
            code="not_found_or_hidden",
            message="Resource was not found.",
        )
    tenant = await tenant_service.resolve_by_subdomain(subdomain)
    result = await presence_service.redeem_token(
        tenant_id=tenant.tenant_id,
        raw_qr_token=payload.qr_token,
        existing_customer_session_token=request.cookies.get(CUSTOMER_SESSION_COOKIE_NAME),
    )
    response.set_cookie(
        key=CUSTOMER_SESSION_COOKIE_NAME,
        value=result.customer_session_token,
        httponly=True,
        secure=cookie_secure(request.app.state.settings),
        samesite="lax",
        expires=result.session_expires_at,
        path="/",
    )
    return result.as_api_payload()


@router.get("/table-presence", response_model=PresenceStateResponse)
async def get_table_presence(
    request: Request,
    presence_service: Annotated[TablePresenceService, Depends(get_table_presence_service)],
) -> dict[str, Any]:
    return (
        await presence_service.get_presence_state(
            customer_session_token=request.cookies.get(CUSTOMER_SESSION_COOKIE_NAME),
        )
    ).as_api_payload()


@router.get("/cart", response_model=CartResponse)
async def get_cart(
    request: Request,
    service: Annotated[CustomerOrderingService, Depends(get_customer_ordering_service)],
) -> dict[str, Any]:
    return (
        await service.get_cart(
            customer_session_token=request.cookies.get(CUSTOMER_SESSION_COOKIE_NAME),
        )
    ).as_api_payload()


@router.post(
    "/cart/items",
    response_model=CartResponse,
    dependencies=[Depends(require_csrf_token)],
)
async def add_or_update_cart_item(
    payload: CartItemWriteRequest,
    request: Request,
    service: Annotated[CustomerOrderingService, Depends(get_customer_ordering_service)],
) -> dict[str, Any]:
    return (
        await service.add_or_update_cart_item(
            customer_session_token=request.cookies.get(CUSTOMER_SESSION_COOKIE_NAME),
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.post(
    "/cart/items/{client_cart_item_id}/remove",
    response_model=CartResponse,
    dependencies=[Depends(require_csrf_token)],
)
async def remove_cart_item(
    client_cart_item_id: str,
    request: Request,
    service: Annotated[CustomerOrderingService, Depends(get_customer_ordering_service)],
) -> dict[str, Any]:
    return (
        await service.remove_cart_item(
            customer_session_token=request.cookies.get(CUSTOMER_SESSION_COOKIE_NAME),
            client_cart_item_id=client_cart_item_id,
        )
    ).as_api_payload()


@router.post(
    "/orders",
    response_model=SubmittedOrderResultResponse,
    dependencies=[Depends(require_csrf_token)],
)
async def submit_order(
    payload: SubmitOrderRequest,
    request: Request,
    service: Annotated[CustomerOrderingService, Depends(get_customer_ordering_service)],
) -> dict[str, Any]:
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key is None or not idempotency_key.strip():
        raise ApiError(
            status_code=400,
            code="idempotency_key_required",
            message="Idempotency-Key header is required.",
        )
    return (
        await service.submit_order(
            customer_session_token=request.cookies.get(CUSTOMER_SESSION_COOKIE_NAME),
            idempotency_key=idempotency_key.strip(),
            command=payload.to_command(),
        )
    ).as_api_payload()
