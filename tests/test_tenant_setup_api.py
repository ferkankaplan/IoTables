from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from iotables.api.tenant_setup import (
    get_menu_catalog_mutation_service,
    get_menu_catalog_query_service,
    get_station_setup_mutation_service,
    get_station_setup_query_service,
    get_venue_layout_mutation_service,
    get_venue_layout_query_service,
)
from iotables.main import create_app
from iotables.modules.tenant_setup.menu_catalog import (
    AvailabilityCommand,
    AvailabilityOverride,
    CategoryWriteCommand,
    MenuCategory,
    MenuSetupCatalog,
    ModifierConfigCommand,
    ModifierGroup,
    ModifierGroupCommand,
    ModifierOption,
    ModifierOptionCommand,
    ProductService,
    ProductUpdateCommand,
    ProductVariant,
    ProductWriteCommand,
    VariantWriteCommand,
    product_to_customer_menu_product,
)
from iotables.modules.tenant_setup.station_setup import Station, StationList, StationWriteCommand
from iotables.modules.tenant_setup.venue_layout import (
    HallTableBoard,
    HallWithTables,
    HallWriteCommand,
    TableWriteCommand,
    VenueTable,
)
from iotables.security.context import ActorContext, ActorType, AppScope, StaffRole

TENANT_ID = UUID("33333333-3333-3333-3333-333333333333")
USER_ID = UUID("44444444-4444-4444-4444-444444444444")
HALL_ID = UUID("55555555-5555-5555-5555-555555555555")
TABLE_ID = UUID("66666666-6666-6666-6666-666666666666")
STATION_ID = UUID("77777777-7777-7777-7777-777777777777")
CATEGORY_ID = UUID("88888888-8888-8888-8888-888888888888")
PRODUCT_ID = UUID("99999999-9999-9999-9999-999999999999")
VARIANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
GROUP_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OPTION_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
OVERRIDE_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


class FakeSessionResolver:
    def __init__(self, actor: ActorContext | None) -> None:
        self.actor = actor

    async def resolve(self, session_token: str) -> ActorContext | None:
        if session_token == "valid":
            return self.actor
        return None


class FakeVenueLayoutQueryService:
    def __init__(self) -> None:
        self.tenant_id: UUID | None = None

    async def get_hall_table_board(self, *, tenant_id: UUID) -> HallTableBoard:
        self.tenant_id = tenant_id
        return HallTableBoard(
            halls=(
                HallWithTables(
                    hall_id=HALL_ID,
                    name="Salon 1",
                    display_order=1,
                    table_number_base=100,
                    enabled=True,
                    tables=(
                        VenueTable(
                            table_id=TABLE_ID,
                            hall_id=HALL_ID,
                            table_number=101,
                            name="Masa 101",
                            display_order=1,
                            mode="physical",
                            enabled=True,
                        ),
                    ),
                ),
            ),
            derived_at=datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
        )


class FakeVenueLayoutMutationService:
    def __init__(self) -> None:
        self.create_hall_args: dict[str, object] | None = None
        self.create_table_args: dict[str, object] | None = None
        self.disable_table_args: dict[str, object] | None = None

    async def create_hall(
        self, *, actor: ActorContext, command: HallWriteCommand
    ) -> HallWithTables:
        self.create_hall_args = {"actor": actor, "command": command}
        return HallWithTables(
            hall_id=HALL_ID,
            name=command.name,
            display_order=command.display_order,
            table_number_base=command.display_order * 100,
            enabled=True,
            tables=(),
        )

    async def create_table(
        self,
        *,
        actor: ActorContext,
        hall_id: UUID,
        command: TableWriteCommand,
    ) -> VenueTable:
        self.create_table_args = {"actor": actor, "hall_id": hall_id, "command": command}
        return VenueTable(
            table_id=TABLE_ID,
            hall_id=hall_id,
            table_number=100 + command.display_order - 1,
            name=command.name,
            display_order=command.display_order,
            mode=command.mode or "virtual_test",
            enabled=True,
        )

    async def disable_table(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        reason: str,
    ) -> VenueTable:
        self.disable_table_args = {"actor": actor, "table_id": table_id, "reason": reason}
        return VenueTable(
            table_id=table_id,
            hall_id=HALL_ID,
            table_number=101,
            name="Masa 101",
            display_order=1,
            mode="physical",
            enabled=False,
        )


class FakeStationSetupQueryService:
    def __init__(self) -> None:
        self.args: dict[str, object] | None = None

    async def list_stations(
        self,
        *,
        tenant_id: UUID,
        include_disabled: bool = False,
    ) -> StationList:
        self.args = {"tenant_id": tenant_id, "include_disabled": include_disabled}
        return StationList(items=(make_station(),))


class FakeStationSetupMutationService:
    def __init__(self) -> None:
        self.create_args: dict[str, object] | None = None
        self.disable_args: dict[str, object] | None = None

    async def create_station(self, *, actor: ActorContext, command: StationWriteCommand) -> Station:
        self.create_args = {"actor": actor, "command": command}
        return make_station(name=command.name, display_order=command.display_order)

    async def disable_station(
        self,
        *,
        actor: ActorContext,
        station_id: UUID,
        reason: str,
    ) -> Station:
        self.disable_args = {"actor": actor, "station_id": station_id, "reason": reason}
        return make_station(enabled=False)


class FakeMenuCatalogQueryService:
    def __init__(self) -> None:
        self.args: dict[str, object] | None = None
        self.get_product_args: dict[str, object] | None = None

    async def list_menu_setup(
        self,
        *,
        tenant_id: UUID,
        include_disabled: bool = False,
    ) -> MenuSetupCatalog:
        self.args = {"tenant_id": tenant_id, "include_disabled": include_disabled}
        return MenuSetupCatalog(
            categories=(make_category(products=(make_product(),)),),
            derived_at=now(),
        )

    async def get_product_service(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        include_disabled: bool = False,
    ) -> ProductService:
        self.get_product_args = {
            "tenant_id": tenant_id,
            "product_id": product_id,
            "include_disabled": include_disabled,
        }
        return make_product()


class FakeMenuCatalogMutationService:
    def __init__(self) -> None:
        self.create_category_args: dict[str, object] | None = None
        self.update_category_args: dict[str, object] | None = None
        self.disable_category_args: dict[str, object] | None = None
        self.create_product_args: dict[str, object] | None = None
        self.update_product_args: dict[str, object] | None = None
        self.disable_product_args: dict[str, object] | None = None
        self.manage_variant_args: dict[str, object] | None = None
        self.manage_modifiers_args: dict[str, object] | None = None
        self.set_availability_args: dict[str, object] | None = None

    async def create_category(
        self,
        *,
        actor: ActorContext,
        command: CategoryWriteCommand,
    ) -> MenuCategory:
        self.create_category_args = {"actor": actor, "command": command}
        return make_category(name=command.name, display_order=command.display_order)

    async def update_category(
        self,
        *,
        actor: ActorContext,
        category_id: UUID,
        command: CategoryWriteCommand,
    ) -> MenuCategory:
        self.update_category_args = {
            "actor": actor,
            "category_id": category_id,
            "command": command,
        }
        return make_category(name=command.name, display_order=command.display_order)

    async def disable_category(
        self,
        *,
        actor: ActorContext,
        category_id: UUID,
        reason: str,
    ) -> MenuCategory:
        self.disable_category_args = {
            "actor": actor,
            "category_id": category_id,
            "reason": reason,
        }
        return make_category(products=(), enabled=False)

    async def create_product_service(
        self,
        *,
        actor: ActorContext,
        command: ProductWriteCommand,
    ) -> ProductService:
        self.create_product_args = {"actor": actor, "command": command}
        variant = command.variants[0]
        return make_product(
            name=command.name,
            category_id=command.category_id,
            station_id=command.station_id,
            variants=(
                make_variant(
                    name=variant.name,
                    price_minor=variant.price_minor,
                    display_order=variant.display_order,
                ),
            ),
        )

    async def update_product_service(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: ProductUpdateCommand,
    ) -> ProductService:
        self.update_product_args = {
            "actor": actor,
            "product_id": product_id,
            "command": command,
        }
        return make_product(
            name=command.name or "Americano",
            category_id=command.category_id or CATEGORY_ID,
            station_id=command.station_id or STATION_ID,
        )

    async def disable_product_service(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        reason: str,
    ) -> ProductService:
        self.disable_product_args = {"actor": actor, "product_id": product_id, "reason": reason}
        return make_product(enabled=False)

    async def manage_variant(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: VariantWriteCommand,
    ) -> ProductVariant:
        self.manage_variant_args = {
            "actor": actor,
            "product_id": product_id,
            "command": command,
        }
        return make_variant(
            name=command.name,
            price_minor=command.price_minor,
            display_order=command.display_order,
        )

    async def manage_modifiers(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: ModifierConfigCommand,
    ) -> tuple[ModifierGroup, ...]:
        self.manage_modifiers_args = {
            "actor": actor,
            "product_id": product_id,
            "command": command,
        }
        return (make_modifier_group(command.groups[0] if command.groups else None),)

    async def set_availability(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: AvailabilityCommand,
    ) -> AvailabilityOverride:
        self.set_availability_args = {
            "actor": actor,
            "product_id": product_id,
            "command": command,
        }
        return make_availability(state=command.state, reason=command.reason)


def now() -> datetime:
    return datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


def make_variant(
    *,
    name: str = "Standart",
    price_minor: int = 10000,
    display_order: int = 1,
) -> ProductVariant:
    return ProductVariant(
        variant_id=VARIANT_ID,
        product_id=PRODUCT_ID,
        name=name,
        price_minor=price_minor,
        currency_code="TRY",
        display_order=display_order,
        is_default=True,
        enabled=True,
    )


def make_product(
    *,
    name: str = "Americano",
    category_id: UUID = CATEGORY_ID,
    station_id: UUID = STATION_ID,
    enabled: bool = True,
    variants: tuple[ProductVariant, ...] | None = None,
    modifier_groups: tuple[ModifierGroup, ...] = (),
    availability: tuple[AvailabilityOverride, ...] = (),
) -> ProductService:
    return ProductService(
        product_id=PRODUCT_ID,
        category_id=category_id,
        station_id=station_id,
        name=name,
        description=None,
        enabled=enabled,
        variants=variants or (make_variant(),),
        modifier_groups=modifier_groups,
        availability=availability,
        created_at=now(),
        updated_at=now(),
    )


def make_category(
    *,
    name: str = "Kahveler",
    display_order: int = 1,
    enabled: bool = True,
    products: tuple[ProductService, ...] = (),
) -> MenuCategory:
    return MenuCategory(
        category_id=CATEGORY_ID,
        name=name,
        display_order=display_order,
        enabled=enabled,
        products=products,
        created_at=now(),
        updated_at=now(),
    )


def make_modifier_group(command: ModifierGroupCommand | None = None) -> ModifierGroup:
    option_command = (
        command.options[0]
        if command and command.options
        else ModifierOptionCommand(name="Süt", price_delta_minor=0)
    )
    group_name = command.name if command else "Ekstra"
    return ModifierGroup(
        group_id=GROUP_ID,
        product_id=PRODUCT_ID,
        name=group_name,
        required=command.required if command else False,
        min_selections=command.min_selections if command else 0,
        max_selections=command.max_selections if command else 1,
        display_order=command.display_order if command else 1,
        options=(
            ModifierOption(
                option_id=OPTION_ID,
                group_id=GROUP_ID,
                name=option_command.name,
                price_delta_minor=option_command.price_delta_minor,
                currency_code=option_command.currency_code,
                available=option_command.available,
                display_order=option_command.display_order,
            ),
        ),
    )


def make_availability(
    *,
    state: str = "unavailable",
    reason: str | None = "bitti",
    variant_id: UUID | None = None,
) -> AvailabilityOverride:
    return AvailabilityOverride(
        override_id=OVERRIDE_ID,
        product_id=PRODUCT_ID,
        variant_id=variant_id,
        state=state,
        reason=reason,
        starts_at=None,
        ends_at=None,
        created_at=now(),
    )


def make_station(
    *,
    name: str = "Mutfak",
    display_order: int = 1,
    enabled: bool = True,
) -> Station:
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    return Station(
        station_id=STATION_ID,
        name=name,
        display_order=display_order,
        enabled=enabled,
        created_at=now,
        updated_at=now,
    )


def make_actor(
    *,
    app_scope: AppScope = AppScope.TENANT,
    roles: frozenset[StaffRole] = frozenset({StaffRole.TENANT_ADMIN}),
) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.TENANT_USER,
        app_scope=app_scope,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        roles=roles,
    )


def make_client(
    *,
    actor: ActorContext | None = None,
    service: FakeVenueLayoutQueryService | None = None,
    mutation_service: FakeVenueLayoutMutationService | None = None,
    station_query_service: FakeStationSetupQueryService | None = None,
    station_mutation_service: FakeStationSetupMutationService | None = None,
    menu_query_service: FakeMenuCatalogQueryService | None = None,
    menu_mutation_service: FakeMenuCatalogMutationService | None = None,
) -> TestClient:
    app = create_app()
    app.state.session_resolver = FakeSessionResolver(actor)
    if service is not None:
        app.dependency_overrides[get_venue_layout_query_service] = lambda: service
    if mutation_service is not None:
        app.dependency_overrides[get_venue_layout_mutation_service] = lambda: mutation_service
    if station_query_service is not None:
        app.dependency_overrides[get_station_setup_query_service] = lambda: station_query_service
    if station_mutation_service is not None:
        app.dependency_overrides[get_station_setup_mutation_service] = lambda: (
            station_mutation_service
        )
    if menu_query_service is not None:
        app.dependency_overrides[get_menu_catalog_query_service] = lambda: menu_query_service
    if menu_mutation_service is not None:
        app.dependency_overrides[get_menu_catalog_mutation_service] = lambda: menu_mutation_service
    client = TestClient(app)
    client.cookies.set("iotables_session", "valid")
    return client


def test_venue_board_requires_tenant_session() -> None:
    client = make_client(actor=None, service=FakeVenueLayoutQueryService())

    response = client.get("/api/tenant-setup/venue/board")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_venue_board_rejects_non_tenant_admin_role() -> None:
    client = make_client(
        actor=make_actor(roles=frozenset({StaffRole.CASHIER})),
        service=FakeVenueLayoutQueryService(),
    )

    response = client.get("/api/tenant-setup/venue/board")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_authorized"


def test_venue_board_uses_actor_tenant_scope() -> None:
    service = FakeVenueLayoutQueryService()
    client = make_client(actor=make_actor(), service=service)

    response = client.get("/api/tenant-setup/venue/board")

    assert response.status_code == 200
    assert response.json() == {
        "halls": [
                {
                    "hallId": str(HALL_ID),
                    "name": "Salon 1",
                    "displayOrder": 1,
                    "tableNumberBase": 100,
                    "enabled": True,
                    "tables": [
                        {
                            "tableId": str(TABLE_ID),
                            "hallId": str(HALL_ID),
                            "tableNumber": 101,
                            "name": "Masa 101",
                            "displayOrder": 1,
                            "mode": "physical",
                            "systemBoundarySlot": False,
                            "enabled": True,
                        }
                    ],
            }
        ],
        "derivedAt": "2026-07-03T12:00:00+00:00",
    }
    assert service.tenant_id == TENANT_ID


def test_create_hall_requires_csrf_token() -> None:
    client = make_client(actor=make_actor(), mutation_service=FakeVenueLayoutMutationService())

    response = client.post(
        "/api/tenant-setup/halls",
        json={"name": "Bahce", "displayOrder": 3},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_required"


def test_create_hall_uses_actor_tenant_admin_scope() -> None:
    service = FakeVenueLayoutMutationService()
    client = make_client(actor=make_actor(), mutation_service=service)

    response = client.post(
        "/api/tenant-setup/halls",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "Bahce", "displayOrder": 3},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Bahce"
    assert response.json()["displayOrder"] == 3
    assert service.create_hall_args is not None
    assert service.create_hall_args["actor"] == make_actor()


def test_create_table_belongs_to_hall_context() -> None:
    service = FakeVenueLayoutMutationService()
    client = make_client(actor=make_actor(), mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/halls/{HALL_ID}/tables",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "Masa 777", "displayOrder": 7},
    )

    assert response.status_code == 200
    assert response.json()["hallId"] == str(HALL_ID)
    assert response.json()["name"] == "Masa 777"
    assert service.create_table_args is not None
    assert service.create_table_args["hall_id"] == HALL_ID


def test_disable_table_requires_reason_and_returns_disabled_table() -> None:
    service = FakeVenueLayoutMutationService()
    client = make_client(actor=make_actor(), mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/tables/{TABLE_ID}/disable",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "closed area"},
    )

    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert service.disable_table_args == {
        "actor": make_actor(),
        "table_id": TABLE_ID,
        "reason": "closed area",
    }


def test_list_stations_uses_actor_tenant_scope() -> None:
    service = FakeStationSetupQueryService()
    client = make_client(actor=make_actor(), station_query_service=service)

    response = client.get("/api/tenant-setup/stations?include_disabled=true")

    assert response.status_code == 200
    assert response.json()["items"][0]["stationId"] == str(STATION_ID)
    assert service.args == {"tenant_id": TENANT_ID, "include_disabled": True}


def test_create_station_requires_csrf_and_returns_station() -> None:
    service = FakeStationSetupMutationService()
    client = make_client(actor=make_actor(), station_mutation_service=service)

    missing_csrf = client.post(
        "/api/tenant-setup/stations",
        json={"name": "Bar", "displayOrder": 2},
    )
    response = client.post(
        "/api/tenant-setup/stations",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "Bar", "displayOrder": 2},
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 200
    assert response.json()["name"] == "Bar"
    assert service.create_args is not None
    assert service.create_args["actor"] == make_actor()


def test_disable_station_requires_reason_and_returns_disabled_station() -> None:
    service = FakeStationSetupMutationService()
    client = make_client(actor=make_actor(), station_mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/stations/{STATION_ID}/disable",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "renovation"},
    )

    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert service.disable_args == {
        "actor": make_actor(),
        "station_id": STATION_ID,
        "reason": "renovation",
    }


def test_list_menu_setup_uses_actor_tenant_scope() -> None:
    service = FakeMenuCatalogQueryService()
    client = make_client(actor=make_actor(), menu_query_service=service)

    response = client.get("/api/tenant-setup/menu?include_disabled=true")

    assert response.status_code == 200
    assert response.json()["categories"][0]["categoryId"] == str(CATEGORY_ID)
    assert response.json()["categories"][0]["products"][0]["productId"] == str(PRODUCT_ID)
    assert service.args == {"tenant_id": TENANT_ID, "include_disabled": True}


def test_create_menu_category_requires_csrf_and_returns_category() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    missing_csrf = client.post(
        "/api/tenant-setup/menu/categories",
        json={"name": "Tatlılar", "displayOrder": 4},
    )
    response = client.post(
        "/api/tenant-setup/menu/categories",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "Tatlılar", "displayOrder": 4},
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 200
    assert response.json()["name"] == "Tatlılar"
    assert service.create_category_args is not None
    assert service.create_category_args["actor"] == make_actor()


def test_create_product_service_binds_category_station_and_initial_variant() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.post(
        "/api/tenant-setup/menu/products",
        headers={"X-CSRF-Token": "csrf"},
        json={
            "categoryId": str(CATEGORY_ID),
            "stationId": str(STATION_ID),
            "name": "Latte",
            "variants": [{"name": "Standart", "priceMinor": 12000}],
        },
    )

    assert response.status_code == 200
    assert response.json()["categoryId"] == str(CATEGORY_ID)
    assert response.json()["stationId"] == str(STATION_ID)
    assert response.json()["variants"][0]["priceMinor"] == 12000
    assert service.create_product_args is not None
    command = service.create_product_args["command"]
    assert isinstance(command, ProductWriteCommand)
    assert command.variants[0] == VariantWriteCommand(name="Standart", price_minor=12000)


def test_update_menu_category_binds_category_id_and_command() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.patch(
        f"/api/tenant-setup/menu/categories/{CATEGORY_ID}",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "Sıcak İçecekler", "displayOrder": 2},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Sıcak İçecekler"
    assert service.update_category_args is not None
    assert service.update_category_args["category_id"] == CATEGORY_ID
    assert service.update_category_args["command"] == CategoryWriteCommand(
        name="Sıcak İçecekler",
        display_order=2,
    )


def test_disable_menu_category_requires_reason() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/menu/categories/{CATEGORY_ID}/disable",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "seasonal"},
    )

    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert service.disable_category_args == {
        "actor": make_actor(),
        "category_id": CATEGORY_ID,
        "reason": "seasonal",
    }


def test_get_product_service_uses_tenant_scope() -> None:
    service = FakeMenuCatalogQueryService()
    client = make_client(actor=make_actor(), menu_query_service=service)

    response = client.get(f"/api/tenant-setup/menu/products/{PRODUCT_ID}")

    assert response.status_code == 200
    assert response.json()["productId"] == str(PRODUCT_ID)
    assert service.get_product_args == {
        "tenant_id": TENANT_ID,
        "product_id": PRODUCT_ID,
        "include_disabled": True,
    }


def test_update_product_service_binds_editable_fields() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.patch(
        f"/api/tenant-setup/menu/products/{PRODUCT_ID}",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "Filtre Kahve", "stationId": str(STATION_ID), "enabled": True},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Filtre Kahve"
    assert service.update_product_args is not None
    command = service.update_product_args["command"]
    assert isinstance(command, ProductUpdateCommand)
    assert command.name == "Filtre Kahve"
    assert command.station_id == STATION_ID


def test_disable_product_service_binds_reason() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/menu/products/{PRODUCT_ID}/disable",
        headers={"X-CSRF-Token": "csrf"},
        json={"reason": "not sold"},
    )

    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert service.disable_product_args == {
        "actor": make_actor(),
        "product_id": PRODUCT_ID,
        "reason": "not sold",
    }


def test_manage_variant_binds_variant_command() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/menu/products/{PRODUCT_ID}/variants",
        headers={"X-CSRF-Token": "csrf"},
        json={
            "variantId": str(VARIANT_ID),
            "name": "Büyük",
            "priceMinor": 15000,
            "displayOrder": 2,
            "isDefault": True,
            "enabled": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Büyük"
    assert service.manage_variant_args is not None
    command = service.manage_variant_args["command"]
    assert isinstance(command, VariantWriteCommand)
    assert command.variant_id == VARIANT_ID
    assert command.price_minor == 15000


def test_manage_modifiers_replaces_product_modifier_config() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/menu/products/{PRODUCT_ID}/modifiers",
        headers={"X-CSRF-Token": "csrf"},
        json={
            "groups": [
                {
                    "name": "Süt seçimi",
                    "required": True,
                    "minSelections": 1,
                    "maxSelections": 1,
                    "displayOrder": 1,
                    "options": [{"name": "Laktozsuz", "priceDeltaMinor": 500}],
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Süt seçimi"
    assert service.manage_modifiers_args is not None
    command = service.manage_modifiers_args["command"]
    assert isinstance(command, ModifierConfigCommand)
    assert command.groups[0].options[0].price_delta_minor == 500


def test_set_availability_binds_override_command() -> None:
    service = FakeMenuCatalogMutationService()
    client = make_client(actor=make_actor(), menu_mutation_service=service)

    response = client.post(
        f"/api/tenant-setup/menu/products/{PRODUCT_ID}/availability",
        headers={"X-CSRF-Token": "csrf"},
        json={"state": "unavailable", "reason": "stok yok"},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "unavailable"
    assert service.set_availability_args is not None
    command = service.set_availability_args["command"]
    assert isinstance(command, AvailabilityCommand)
    assert command.reason == "stok yok"


def test_customer_menu_product_hides_product_unavailable_override() -> None:
    product = make_product(availability=(make_availability(state="unavailable"),))

    assert product_to_customer_menu_product(product) is None


def test_customer_menu_product_hides_unavailable_default_variant() -> None:
    product = make_product(
        variants=(make_variant(),),
        availability=(make_availability(state="unavailable", variant_id=VARIANT_ID),),
    )

    assert product_to_customer_menu_product(product) is None


def test_customer_menu_product_hides_required_modifier_without_enough_options() -> None:
    product = make_product(
        modifier_groups=(
            ModifierGroup(
                group_id=GROUP_ID,
                product_id=PRODUCT_ID,
                name="Pişirme",
                required=True,
                min_selections=1,
                max_selections=1,
                display_order=1,
                options=(),
            ),
        )
    )

    assert product_to_customer_menu_product(product) is None
