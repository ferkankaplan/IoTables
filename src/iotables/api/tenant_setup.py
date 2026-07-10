from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.session import get_database_session
from iotables.modules.tenant_setup.menu_catalog import (
    AvailabilityCommand,
    CategoryWriteCommand,
    MenuCatalogMutationService,
    MenuCatalogQueryService,
    ModifierConfigCommand,
    ModifierGroupCommand,
    ModifierOptionCommand,
    ProductUpdateCommand,
    ProductWriteCommand,
    VariantWriteCommand,
)
from iotables.modules.tenant_setup.station_setup import (
    StationSetupMutationService,
    StationSetupQueryService,
    StationWriteCommand,
)
from iotables.modules.tenant_setup.table_display_provisioning import (
    DisplayFirmwareCommand,
    TableDisplayProvisioningService,
)
from iotables.modules.tenant_setup.venue_layout import (
    HallWriteCommand,
    TableWriteCommand,
    VenueLayoutMutationService,
    VenueLayoutQueryService,
)
from iotables.security.context import ActorContext, AppScope, StaffRole
from iotables.security.dependencies import require_app_scope, require_csrf_token

TENANT_SCOPE_DEP = Depends(require_app_scope(AppScope.TENANT))
CSRF_DEP = Depends(require_csrf_token)

router = APIRouter(prefix="/tenant-setup", tags=["Tenant Setup"])


class VenueTableResponse(BaseModel):
    table_id: str = Field(alias="tableId")
    hall_id: str = Field(alias="hallId")
    table_number: int = Field(alias="tableNumber")
    name: str
    display_order: int = Field(alias="displayOrder")
    mode: str
    system_boundary_slot: bool = Field(alias="systemBoundarySlot")
    enabled: bool


class HallWithTablesResponse(BaseModel):
    hall_id: str = Field(alias="hallId")
    name: str
    display_order: int = Field(alias="displayOrder")
    table_number_base: int = Field(alias="tableNumberBase")
    enabled: bool
    tables: list[VenueTableResponse]


class HallTableBoardResponse(BaseModel):
    halls: list[HallWithTablesResponse]
    derived_at: str = Field(alias="derivedAt")


class StationResponse(BaseModel):
    station_id: str = Field(alias="stationId")
    name: str
    display_order: int = Field(alias="displayOrder")
    enabled: bool
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class StationListResponse(BaseModel):
    items: list[StationResponse]


class ProductVariantResponse(BaseModel):
    variant_id: str = Field(alias="variantId")
    product_id: str = Field(alias="productId")
    name: str
    price_minor: int = Field(alias="priceMinor")
    currency_code: str = Field(alias="currencyCode")
    display_order: int = Field(alias="displayOrder")
    is_default: bool = Field(alias="isDefault")
    enabled: bool


class ModifierOptionResponse(BaseModel):
    option_id: str = Field(alias="optionId")
    group_id: str = Field(alias="groupId")
    name: str
    price_delta_minor: int = Field(alias="priceDeltaMinor")
    currency_code: str = Field(alias="currencyCode")
    available: bool
    display_order: int = Field(alias="displayOrder")


class ModifierGroupResponse(BaseModel):
    group_id: str = Field(alias="groupId")
    product_id: str = Field(alias="productId")
    name: str
    required: bool
    min_selections: int = Field(alias="minSelections")
    max_selections: int = Field(alias="maxSelections")
    display_order: int = Field(alias="displayOrder")
    options: list[ModifierOptionResponse]


class AvailabilityOverrideResponse(BaseModel):
    override_id: str = Field(alias="overrideId")
    product_id: str = Field(alias="productId")
    variant_id: str | None = Field(alias="variantId")
    state: str
    reason: str | None
    starts_at: str | None = Field(alias="startsAt")
    ends_at: str | None = Field(alias="endsAt")
    created_at: str = Field(alias="createdAt")


class ProductServiceResponse(BaseModel):
    product_id: str = Field(alias="productId")
    category_id: str = Field(alias="categoryId")
    station_id: str = Field(alias="stationId")
    name: str
    description: str | None
    enabled: bool
    variants: list[ProductVariantResponse]
    modifier_groups: list[ModifierGroupResponse] = Field(alias="modifierGroups")
    availability: list[AvailabilityOverrideResponse]
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class MenuCategoryResponse(BaseModel):
    category_id: str = Field(alias="categoryId")
    name: str
    display_order: int = Field(alias="displayOrder")
    enabled: bool
    products: list[ProductServiceResponse]
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class MenuSetupCatalogResponse(BaseModel):
    categories: list[MenuCategoryResponse]
    derived_at: str = Field(alias="derivedAt")


class HallWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    display_order: int = Field(alias="displayOrder", gt=0)

    def to_command(self) -> HallWriteCommand:
        return HallWriteCommand(name=self.name, display_order=self.display_order)


class TableWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    display_order: int = Field(alias="displayOrder", gt=0)
    hall_id: UUID | None = Field(default=None, alias="hallId")
    enabled: bool | None = None
    mode: str | None = None

    def to_command(self) -> TableWriteCommand:
        return TableWriteCommand(
            name=self.name,
            display_order=self.display_order,
            hall_id=self.hall_id,
            enabled=self.enabled,
            mode=self.mode,
        )


class DisableRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reason: str = Field(min_length=1)


class DisplayFirmwareCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    wifi_ssid: str = Field(alias="wifiSsid", min_length=1)
    wifi_password: str = Field(alias="wifiPassword", min_length=1)

    def to_command(self) -> DisplayFirmwareCommand:
        return DisplayFirmwareCommand(
            wifi_ssid=self.wifi_ssid,
            wifi_password=self.wifi_password,
        )


class DisplayFirmwareCreatedResponse(BaseModel):
    firmware_id: str = Field(alias="firmwareId")
    file_name: str = Field(alias="fileName")
    credential_id: str = Field(alias="credentialId")
    table_id: str = Field(alias="tableId")
    expires_at: str = Field(alias="expiresAt")
    firmware_content: str = Field(alias="firmwareContent")


class StationWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    display_order: int = Field(alias="displayOrder", gt=0)

    def to_command(self) -> StationWriteCommand:
        return StationWriteCommand(name=self.name, display_order=self.display_order)


class CategoryWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    display_order: int = Field(alias="displayOrder", gt=0)

    def to_command(self) -> CategoryWriteCommand:
        return CategoryWriteCommand(name=self.name, display_order=self.display_order)


class VariantWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    price_minor: int = Field(alias="priceMinor", ge=0)
    currency_code: str = Field(default="TRY", alias="currencyCode", min_length=3, max_length=3)
    display_order: int = Field(default=1, alias="displayOrder", gt=0)
    is_default: bool = Field(default=True, alias="isDefault")
    enabled: bool = True
    variant_id: UUID | None = Field(default=None, alias="variantId")

    def to_command(self) -> VariantWriteCommand:
        return VariantWriteCommand(
            name=self.name,
            price_minor=self.price_minor,
            currency_code=self.currency_code.upper(),
            display_order=self.display_order,
            is_default=self.is_default,
            enabled=self.enabled,
            variant_id=self.variant_id,
        )


class ProductWriteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category_id: UUID = Field(alias="categoryId")
    station_id: UUID = Field(alias="stationId")
    name: str = Field(min_length=1)
    description: str | None = None
    variants: list[VariantWriteRequest] = Field(min_length=1)

    def to_command(self) -> ProductWriteCommand:
        return ProductWriteCommand(
            category_id=self.category_id,
            station_id=self.station_id,
            name=self.name,
            description=self.description,
            variants=tuple(variant.to_command() for variant in self.variants),
        )


class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category_id: UUID | None = Field(default=None, alias="categoryId")
    station_id: UUID | None = Field(default=None, alias="stationId")
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    enabled: bool | None = None

    def to_command(self) -> ProductUpdateCommand:
        return ProductUpdateCommand(
            category_id=self.category_id,
            station_id=self.station_id,
            name=self.name,
            description=self.description,
            description_supplied="description" in self.model_fields_set,
            enabled=self.enabled,
        )


class ModifierOptionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    price_delta_minor: int = Field(default=0, alias="priceDeltaMinor", ge=0)
    currency_code: str = Field(default="TRY", alias="currencyCode", min_length=3, max_length=3)
    available: bool = True
    display_order: int = Field(default=1, alias="displayOrder", gt=0)

    def to_command(self) -> ModifierOptionCommand:
        return ModifierOptionCommand(
            name=self.name,
            price_delta_minor=self.price_delta_minor,
            currency_code=self.currency_code.upper(),
            available=self.available,
            display_order=self.display_order,
        )


class ModifierGroupRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    required: bool = False
    min_selections: int = Field(default=0, alias="minSelections", ge=0)
    max_selections: int = Field(default=1, alias="maxSelections", ge=0)
    display_order: int = Field(default=1, alias="displayOrder", gt=0)
    options: list[ModifierOptionRequest] = Field(default_factory=list)

    def to_command(self) -> ModifierGroupCommand:
        return ModifierGroupCommand(
            name=self.name,
            required=self.required,
            min_selections=self.min_selections,
            max_selections=self.max_selections,
            display_order=self.display_order,
            options=tuple(option.to_command() for option in self.options),
        )


class ModifierConfigRequest(BaseModel):
    groups: list[ModifierGroupRequest] = Field(default_factory=list)

    def to_command(self) -> ModifierConfigCommand:
        return ModifierConfigCommand(groups=tuple(group.to_command() for group in self.groups))


class AvailabilityRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    variant_id: UUID | None = Field(default=None, alias="variantId")
    state: str = Field(pattern="^(available|unavailable)$")
    reason: str | None = None
    starts_at: datetime | None = Field(default=None, alias="startsAt")
    ends_at: datetime | None = Field(default=None, alias="endsAt")

    def to_command(self) -> AvailabilityCommand:
        return AvailabilityCommand(
            variant_id=self.variant_id,
            state=self.state,
            reason=self.reason,
            starts_at=self.starts_at,
            ends_at=self.ends_at,
        )


def get_venue_layout_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> VenueLayoutQueryService:
    return VenueLayoutQueryService(session)


def get_venue_layout_mutation_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> VenueLayoutMutationService:
    return VenueLayoutMutationService(session)


def get_station_setup_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> StationSetupQueryService:
    return StationSetupQueryService(session)


def get_station_setup_mutation_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> StationSetupMutationService:
    return StationSetupMutationService(session)


def get_menu_catalog_query_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> MenuCatalogQueryService:
    return MenuCatalogQueryService(session)


def get_menu_catalog_mutation_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> MenuCatalogMutationService:
    return MenuCatalogMutationService(session)


def get_table_display_provisioning_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TableDisplayProvisioningService:
    return TableDisplayProvisioningService(session)


def require_tenant_admin(actor: ActorContext) -> None:
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


@router.get("/venue/board", response_model=HallTableBoardResponse)
async def get_hall_table_board(
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutQueryService, Depends(get_venue_layout_query_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (await service.get_hall_table_board(tenant_id=actor.tenant_id)).as_api_payload()


@router.post(
    "/halls",
    response_model=HallWithTablesResponse,
    dependencies=[CSRF_DEP],
)
async def create_hall(
    payload: HallWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutMutationService, Depends(get_venue_layout_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (await service.create_hall(actor=actor, command=payload.to_command())).as_api_payload()


@router.patch(
    "/halls/{hall_id}",
    response_model=HallWithTablesResponse,
    dependencies=[CSRF_DEP],
)
async def update_hall(
    hall_id: UUID,
    payload: HallWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutMutationService, Depends(get_venue_layout_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.update_hall(actor=actor, hall_id=hall_id, command=payload.to_command())
    ).as_api_payload()


@router.post(
    "/halls/{hall_id}/disable",
    response_model=HallWithTablesResponse,
    dependencies=[CSRF_DEP],
)
async def disable_hall(
    hall_id: UUID,
    payload: DisableRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutMutationService, Depends(get_venue_layout_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.disable_hall(actor=actor, hall_id=hall_id, reason=payload.reason)
    ).as_api_payload()


@router.post(
    "/halls/{hall_id}/tables",
    response_model=VenueTableResponse,
    dependencies=[CSRF_DEP],
)
async def create_table(
    hall_id: UUID,
    payload: TableWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutMutationService, Depends(get_venue_layout_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.create_table(actor=actor, hall_id=hall_id, command=payload.to_command())
    ).as_api_payload()


@router.patch(
    "/tables/{table_id}",
    response_model=VenueTableResponse,
    dependencies=[CSRF_DEP],
)
async def update_table(
    table_id: UUID,
    payload: TableWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutMutationService, Depends(get_venue_layout_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.update_table(actor=actor, table_id=table_id, command=payload.to_command())
    ).as_api_payload()


@router.post(
    "/tables/{table_id}/disable",
    response_model=VenueTableResponse,
    dependencies=[CSRF_DEP],
)
async def disable_table(
    table_id: UUID,
    payload: DisableRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[VenueLayoutMutationService, Depends(get_venue_layout_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.disable_table(actor=actor, table_id=table_id, reason=payload.reason)
    ).as_api_payload()


@router.post(
    "/tables/{table_id}/display-firmware",
    response_model=DisplayFirmwareCreatedResponse,
    dependencies=[CSRF_DEP],
)
async def create_display_firmware(
    table_id: UUID,
    payload: DisplayFirmwareCreateRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[
        TableDisplayProvisioningService,
        Depends(get_table_display_provisioning_service),
    ],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.generate_firmware(
            actor=actor,
            table_id=table_id,
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.get("/stations", response_model=StationListResponse)
async def list_stations(
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[StationSetupQueryService, Depends(get_station_setup_query_service)],
    include_disabled: bool = False,
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.list_stations(
            tenant_id=actor.tenant_id,
            include_disabled=include_disabled,
        )
    ).as_api_payload()


@router.post(
    "/stations",
    response_model=StationResponse,
    dependencies=[CSRF_DEP],
)
async def create_station(
    payload: StationWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[StationSetupMutationService, Depends(get_station_setup_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.create_station(actor=actor, command=payload.to_command())
    ).as_api_payload()


@router.patch(
    "/stations/{station_id}",
    response_model=StationResponse,
    dependencies=[CSRF_DEP],
)
async def update_station(
    station_id: UUID,
    payload: StationWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[StationSetupMutationService, Depends(get_station_setup_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.update_station(
            actor=actor,
            station_id=station_id,
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.post(
    "/stations/{station_id}/disable",
    response_model=StationResponse,
    dependencies=[CSRF_DEP],
)
async def disable_station(
    station_id: UUID,
    payload: DisableRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[StationSetupMutationService, Depends(get_station_setup_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.disable_station(actor=actor, station_id=station_id, reason=payload.reason)
    ).as_api_payload()


@router.get("/menu", response_model=MenuSetupCatalogResponse)
async def list_menu_setup(
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogQueryService, Depends(get_menu_catalog_query_service)],
    include_disabled: bool = False,
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.list_menu_setup(
            tenant_id=actor.tenant_id,
            include_disabled=include_disabled,
        )
    ).as_api_payload()


@router.post(
    "/menu/categories",
    response_model=MenuCategoryResponse,
    dependencies=[CSRF_DEP],
)
async def create_category(
    payload: CategoryWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    category = await service.create_category(actor=actor, command=payload.to_command())
    return category.as_api_payload()


@router.patch(
    "/menu/categories/{category_id}",
    response_model=MenuCategoryResponse,
    dependencies=[CSRF_DEP],
)
async def update_category(
    category_id: UUID,
    payload: CategoryWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.update_category(
            actor=actor,
            category_id=category_id,
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.post(
    "/menu/categories/{category_id}/disable",
    response_model=MenuCategoryResponse,
    dependencies=[CSRF_DEP],
)
async def disable_category(
    category_id: UUID,
    payload: DisableRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.disable_category(
            actor=actor,
            category_id=category_id,
            reason=payload.reason,
        )
    ).as_api_payload()


@router.post(
    "/menu/products",
    response_model=ProductServiceResponse,
    dependencies=[CSRF_DEP],
)
async def create_product_service(
    payload: ProductWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.create_product_service(actor=actor, command=payload.to_command())
    ).as_api_payload()


@router.get("/menu/products/{product_id}", response_model=ProductServiceResponse)
async def get_product_service(
    product_id: UUID,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogQueryService, Depends(get_menu_catalog_query_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.get_product_service(
            tenant_id=actor.tenant_id,
            product_id=product_id,
            include_disabled=True,
        )
    ).as_api_payload()


@router.patch(
    "/menu/products/{product_id}",
    response_model=ProductServiceResponse,
    dependencies=[CSRF_DEP],
)
async def update_product_service(
    product_id: UUID,
    payload: ProductUpdateRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.update_product_service(
            actor=actor,
            product_id=product_id,
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.post(
    "/menu/products/{product_id}/disable",
    response_model=ProductServiceResponse,
    dependencies=[CSRF_DEP],
)
async def disable_product_service(
    product_id: UUID,
    payload: DisableRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.disable_product_service(
            actor=actor,
            product_id=product_id,
            reason=payload.reason,
        )
    ).as_api_payload()


@router.post(
    "/menu/products/{product_id}/variants",
    response_model=ProductVariantResponse,
    dependencies=[CSRF_DEP],
)
async def manage_variant(
    product_id: UUID,
    payload: VariantWriteRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.manage_variant(
            actor=actor,
            product_id=product_id,
            command=payload.to_command(),
        )
    ).as_api_payload()


@router.post(
    "/menu/products/{product_id}/modifiers",
    response_model=list[ModifierGroupResponse],
    dependencies=[CSRF_DEP],
)
async def manage_modifiers(
    product_id: UUID,
    payload: ModifierConfigRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> list[dict[str, Any]]:
    require_tenant_admin(actor)
    groups = await service.manage_modifiers(
        actor=actor,
        product_id=product_id,
        command=payload.to_command(),
    )
    return [group.as_api_payload() for group in groups]


@router.post(
    "/menu/products/{product_id}/availability",
    response_model=AvailabilityOverrideResponse,
    dependencies=[CSRF_DEP],
)
async def set_availability(
    product_id: UUID,
    payload: AvailabilityRequest,
    actor: Annotated[ActorContext, TENANT_SCOPE_DEP],
    service: Annotated[MenuCatalogMutationService, Depends(get_menu_catalog_mutation_service)],
) -> dict[str, Any]:
    require_tenant_admin(actor)
    return (
        await service.set_availability(
            actor=actor,
            product_id=product_id,
            command=payload.to_command(),
        )
    ).as_api_payload()
