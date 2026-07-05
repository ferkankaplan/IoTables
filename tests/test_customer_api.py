from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.customer import (
    get_customer_menu_catalog_query_service,
    get_customer_ordering_service,
    get_customer_tenant_registry_query_service,
    get_table_presence_service,
)
from iotables.api.errors import ApiError
from iotables.main import create_app
from iotables.modules.ordering.customer_ordering import (
    CartItemWriteCommand,
    CustomerCart,
    CustomerCartItem,
    SubmitOrderCommand,
    SubmittedOrderItem,
    SubmittedOrderResult,
)
from iotables.modules.ordering.table_presence import (
    CUSTOMER_SESSION_COOKIE_NAME,
    PresenceRedeemResult,
    PresenceState,
)
from iotables.modules.platform.provisioning import TenantContext
from iotables.modules.tenant_setup.menu_catalog import (
    CustomerMenu,
    CustomerMenuCategory,
    CustomerMenuModifierGroup,
    CustomerMenuOption,
    CustomerMenuProduct,
    CustomerMenuVariant,
)

TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
CATEGORY_ID = UUID("88888888-8888-8888-8888-888888888888")
PRODUCT_ID = UUID("99999999-9999-9999-9999-999999999999")
VARIANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
GROUP_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OPTION_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
CUSTOMER_SESSION_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
TABLE_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
HALL_ID = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")


class FakeTenantRegistryQueryService:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.subdomain: str | None = None
        self.unavailable = unavailable

    async def resolve_by_subdomain(self, subdomain: str) -> TenantContext:
        self.subdomain = subdomain
        if self.unavailable:
            raise ApiError(
                status_code=503,
                code="tenant_unavailable",
                message="Tenant is unavailable.",
            )
        return TenantContext(
            tenant_id=TENANT_ID,
            name="Cafe Demo",
            subdomain=subdomain,
            status="active",
            sector="cafe",
            capacity=24,
            address=None,
        )


class FakeMenuCatalogQueryService:
    def __init__(self) -> None:
        self.tenant_id: UUID | None = None

    async def get_customer_menu(self, *, tenant_id: UUID) -> CustomerMenu:
        self.tenant_id = tenant_id
        return CustomerMenu(
            categories=(
                CustomerMenuCategory(
                    category_id=CATEGORY_ID,
                    name="Kahveler",
                    display_order=1,
                    products=(
                        CustomerMenuProduct(
                            product_id=PRODUCT_ID,
                            category_id=CATEGORY_ID,
                            name="Americano",
                            description=None,
                            variants=(
                                CustomerMenuVariant(
                                    variant_id=VARIANT_ID,
                                    name="Standart",
                                    price_minor=10000,
                                    currency_code="TRY",
                                    display_order=1,
                                    is_default=True,
                                ),
                            ),
                            modifier_groups=(
                                CustomerMenuModifierGroup(
                                    group_id=GROUP_ID,
                                    name="Süt",
                                    required=False,
                                    min_selections=0,
                                    max_selections=1,
                                    display_order=1,
                                    options=(
                                        CustomerMenuOption(
                                            option_id=OPTION_ID,
                                            name="Laktozsuz",
                                            price_delta_minor=500,
                                            currency_code="TRY",
                                            display_order=1,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            derived_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        )


class FakeTablePresenceService:
    def __init__(self) -> None:
        self.redeem_args: dict[str, object] | None = None
        self.state_token: str | None = None

    async def redeem_token(
        self,
        *,
        tenant_id: UUID,
        raw_qr_token: str,
        existing_customer_session_token: str | None,
    ) -> PresenceRedeemResult:
        self.redeem_args = {
            "tenant_id": tenant_id,
            "raw_qr_token": raw_qr_token,
            "existing_customer_session_token": existing_customer_session_token,
        }
        return PresenceRedeemResult(
            customer_ordering_session_id=CUSTOMER_SESSION_ID,
            table_id=TABLE_ID,
            hall_id=HALL_ID,
            fresh_until=datetime(2026, 7, 3, 12, 2, tzinfo=UTC),
            session_expires_at=datetime(2026, 7, 3, 12, 30, tzinfo=UTC),
            customer_session_token="new-customer-session",
            cart_preserved=existing_customer_session_token is not None,
        )

    async def get_presence_state(
        self,
        *,
        customer_session_token: str | None,
    ) -> PresenceState:
        self.state_token = customer_session_token
        return PresenceState(
            customer_ordering_session_id=CUSTOMER_SESSION_ID,
            table_id=TABLE_ID,
            hall_id=HALL_ID,
            fresh_until=datetime(2026, 7, 3, 12, 2, tzinfo=UTC),
            fresh=True,
        )


class FakeCustomerOrderingService:
    def __init__(self) -> None:
        self.get_token: str | None = None
        self.add_args: dict[str, object] | None = None
        self.remove_args: dict[str, object] | None = None
        self.submit_args: dict[str, object] | None = None

    async def get_cart(self, *, customer_session_token: str | None) -> CustomerCart:
        self.get_token = customer_session_token
        return make_cart()

    async def add_or_update_cart_item(
        self,
        *,
        customer_session_token: str | None,
        command: CartItemWriteCommand,
    ) -> CustomerCart:
        self.add_args = {
            "customer_session_token": customer_session_token,
            "command": command,
        }
        return make_cart(items=(make_cart_item(command=command),))

    async def remove_cart_item(
        self,
        *,
        customer_session_token: str | None,
        client_cart_item_id: str,
    ) -> CustomerCart:
        self.remove_args = {
            "customer_session_token": customer_session_token,
            "client_cart_item_id": client_cart_item_id,
        }
        return make_cart(items=())

    async def submit_order(
        self,
        *,
        customer_session_token: str | None,
        idempotency_key: str,
        command: SubmitOrderCommand,
    ) -> SubmittedOrderResult:
        self.submit_args = {
            "customer_session_token": customer_session_token,
            "idempotency_key": idempotency_key,
            "command": command,
        }
        return SubmittedOrderResult(
            order_id=UUID("22222222-2222-2222-2222-222222222222"),
            table_session_id=UUID("33333333-3333-3333-3333-333333333334"),
            check_id=UUID("44444444-4444-4444-4444-444444444445"),
            items=(
                SubmittedOrderItem(
                    order_item_id=UUID("55555555-5555-5555-5555-555555555556"),
                    product_id=PRODUCT_ID,
                    variant_id=VARIANT_ID,
                    station_id=UUID("77777777-7777-7777-7777-777777777777"),
                    name="Americano",
                    variant_name="Standart",
                    quantity=1,
                    unit_price_minor=10000,
                    note=None,
                ),
            ),
            cart_cleared=True,
            duplicate=False,
        )


def make_cart_item(command: CartItemWriteCommand | None = None) -> CustomerCartItem:
    return CustomerCartItem(
        client_cart_item_id=command.client_cart_item_id if command else "item-1",
        product_id=command.product_id if command else PRODUCT_ID,
        variant_id=command.variant_id if command else VARIANT_ID,
        quantity=command.quantity if command else 1,
        selected_modifiers=command.modifier_option_ids if command else (),
        note=command.note if command else None,
        estimated_price_minor=10000,
    )


def make_cart(*, items: tuple[CustomerCartItem, ...] = ()) -> CustomerCart:
    return CustomerCart(
        cart_id=UUID("11111111-1111-1111-1111-111111111111"),
        version="v1",
        items=items,
        display_subtotal_minor=sum(item.estimated_price_minor for item in items),
        currency="TRY",
        updated_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    )


def make_client(
    *,
    tenant_service: FakeTenantRegistryQueryService | None = None,
    menu_service: FakeMenuCatalogQueryService | None = None,
    presence_service: FakeTablePresenceService | None = None,
    ordering_service: FakeCustomerOrderingService | None = None,
) -> TestClient:
    app = create_app()
    tenant_service = tenant_service or FakeTenantRegistryQueryService()
    menu_service = menu_service or FakeMenuCatalogQueryService()
    presence_service = presence_service or FakeTablePresenceService()
    ordering_service = ordering_service or FakeCustomerOrderingService()
    app.dependency_overrides[get_customer_tenant_registry_query_service] = lambda: tenant_service
    app.dependency_overrides[get_customer_menu_catalog_query_service] = lambda: menu_service
    app.dependency_overrides[get_table_presence_service] = lambda: presence_service
    app.dependency_overrides[get_customer_ordering_service] = lambda: ordering_service
    return TestClient(app)


def test_customer_menu_resolves_tenant_from_subdomain_and_returns_public_menu() -> None:
    tenant_service = FakeTenantRegistryQueryService()
    menu_service = FakeMenuCatalogQueryService()
    client = make_client(tenant_service=tenant_service, menu_service=menu_service)

    response = client.get("/api/customer/menu", headers={"X-Tenant-Subdomain": "demo-cafe"})

    assert response.status_code == 200
    assert tenant_service.subdomain == "demo-cafe"
    assert menu_service.tenant_id == TENANT_ID
    product = response.json()["categories"][0]["products"][0]
    assert product["name"] == "Americano"
    assert product["variants"][0]["priceMinor"] == 10000
    assert product["modifierGroups"][0]["options"][0]["priceDeltaMinor"] == 500
    assert "stationId" not in product
    assert "enabled" not in product


def test_customer_menu_requires_tenant_host_context() -> None:
    client = make_client()

    response = client.get("/api/customer/menu")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found_or_hidden"


def test_customer_menu_blocks_unavailable_tenant() -> None:
    client = make_client(tenant_service=FakeTenantRegistryQueryService(unavailable=True))

    response = client.get("/api/customer/menu", headers={"X-Tenant-Subdomain": "demo-cafe"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "tenant_unavailable"


def test_redeem_table_presence_sets_customer_session_cookie() -> None:
    tenant_service = FakeTenantRegistryQueryService()
    presence_service = FakeTablePresenceService()
    client = make_client(tenant_service=tenant_service, presence_service=presence_service)

    response = client.post(
        "/api/customer/table-presence/redeem",
        headers={"X-Tenant-Subdomain": "demo-cafe"},
        json={"qrToken": "raw-qr-token"},
    )

    assert response.status_code == 200
    assert response.json()["customerOrderingSessionId"] == str(CUSTOMER_SESSION_ID)
    assert response.json()["cartPreserved"] is False
    assert presence_service.redeem_args == {
        "tenant_id": TENANT_ID,
        "raw_qr_token": "raw-qr-token",
        "existing_customer_session_token": None,
    }
    assert f"{CUSTOMER_SESSION_COOKIE_NAME}=new-customer-session" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


def test_redeem_table_presence_preserves_compatible_existing_cookie() -> None:
    presence_service = FakeTablePresenceService()
    client = make_client(presence_service=presence_service)
    client.cookies.set(CUSTOMER_SESSION_COOKIE_NAME, "existing-customer-session")

    response = client.post(
        "/api/customer/table-presence/redeem",
        headers={"X-Tenant-Subdomain": "demo-cafe"},
        json={"qrToken": "raw-qr-token"},
    )

    assert response.status_code == 200
    assert response.json()["cartPreserved"] is True
    assert presence_service.redeem_args is not None
    assert (
        presence_service.redeem_args["existing_customer_session_token"]
        == "existing-customer-session"
    )


def test_get_table_presence_uses_customer_session_cookie() -> None:
    presence_service = FakeTablePresenceService()
    client = make_client(presence_service=presence_service)
    client.cookies.set(CUSTOMER_SESSION_COOKIE_NAME, "customer-session")

    response = client.get("/api/customer/table-presence")

    assert response.status_code == 200
    assert response.json()["fresh"] is True
    assert presence_service.state_token == "customer-session"


def test_get_cart_uses_customer_session_cookie() -> None:
    ordering_service = FakeCustomerOrderingService()
    client = make_client(ordering_service=ordering_service)
    client.cookies.set(CUSTOMER_SESSION_COOKIE_NAME, "customer-session")

    response = client.get("/api/customer/cart")

    assert response.status_code == 200
    assert response.json()["cartId"] == "11111111-1111-1111-1111-111111111111"
    assert ordering_service.get_token == "customer-session"


def test_add_cart_item_requires_csrf_and_ignores_client_price() -> None:
    ordering_service = FakeCustomerOrderingService()
    client = make_client(ordering_service=ordering_service)
    client.cookies.set(CUSTOMER_SESSION_COOKIE_NAME, "customer-session")
    payload = {
        "clientCartItemId": "item-1",
        "productId": str(PRODUCT_ID),
        "variantId": str(VARIANT_ID),
        "modifierOptionIds": [str(OPTION_ID)],
        "quantity": 2,
        "note": "az sıcak",
        "estimatedPriceMinor": 1,
    }

    missing_csrf = client.post("/api/customer/cart/items", json=payload)
    response = client.post(
        "/api/customer/cart/items",
        headers={"X-CSRF-Token": "csrf"},
        json=payload,
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 200
    assert response.json()["items"][0]["estimatedPriceMinor"] == 10000
    assert ordering_service.add_args is not None
    command = ordering_service.add_args["command"]
    assert isinstance(command, CartItemWriteCommand)
    assert command.quantity == 2
    assert command.modifier_option_ids == (OPTION_ID,)


def test_remove_cart_item_is_idempotent_command() -> None:
    ordering_service = FakeCustomerOrderingService()
    client = make_client(ordering_service=ordering_service)
    client.cookies.set(CUSTOMER_SESSION_COOKIE_NAME, "customer-session")

    response = client.post(
        "/api/customer/cart/items/item-1/remove",
        headers={"X-CSRF-Token": "csrf"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert ordering_service.remove_args == {
        "customer_session_token": "customer-session",
        "client_cart_item_id": "item-1",
    }


def test_submit_order_requires_csrf_and_idempotency_key() -> None:
    ordering_service = FakeCustomerOrderingService()
    client = make_client(ordering_service=ordering_service)
    client.cookies.set(CUSTOMER_SESSION_COOKIE_NAME, "customer-session")
    payload = {"cartVersion": "v1", "cartItemIds": ["item-1"]}

    missing_csrf = client.post(
        "/api/customer/orders",
        headers={"Idempotency-Key": "submit-1"},
        json=payload,
    )
    missing_key = client.post(
        "/api/customer/orders",
        headers={"X-CSRF-Token": "csrf"},
        json=payload,
    )
    response = client.post(
        "/api/customer/orders",
        headers={"X-CSRF-Token": "csrf", "Idempotency-Key": "submit-1"},
        json=payload,
    )

    assert missing_csrf.status_code == 403
    assert missing_key.status_code == 400
    assert response.status_code == 200
    assert response.json()["cartCleared"] is True
    assert ordering_service.submit_args is not None
    command = ordering_service.submit_args["command"]
    assert isinstance(command, SubmitOrderCommand)
    assert command.cart_item_ids == ("item-1",)
