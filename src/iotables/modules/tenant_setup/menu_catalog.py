from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    audit_events,
    availability_overrides,
    menu_categories,
    modifier_groups,
    modifier_options,
    product_services,
    product_variants,
    stations,
)
from iotables.security.context import ActorContext


@dataclass(frozen=True)
class ProductVariant:
    variant_id: UUID
    product_id: UUID
    name: str
    price_minor: int
    currency_code: str
    display_order: int
    is_default: bool
    enabled: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "variantId": str(self.variant_id),
            "productId": str(self.product_id),
            "name": self.name,
            "priceMinor": self.price_minor,
            "currencyCode": self.currency_code,
            "displayOrder": self.display_order,
            "isDefault": self.is_default,
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class ModifierOption:
    option_id: UUID
    group_id: UUID
    name: str
    price_delta_minor: int
    currency_code: str
    available: bool
    display_order: int

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "optionId": str(self.option_id),
            "groupId": str(self.group_id),
            "name": self.name,
            "priceDeltaMinor": self.price_delta_minor,
            "currencyCode": self.currency_code,
            "available": self.available,
            "displayOrder": self.display_order,
        }


@dataclass(frozen=True)
class ModifierGroup:
    group_id: UUID
    product_id: UUID
    name: str
    required: bool
    min_selections: int
    max_selections: int
    display_order: int
    options: tuple[ModifierOption, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "groupId": str(self.group_id),
            "productId": str(self.product_id),
            "name": self.name,
            "required": self.required,
            "minSelections": self.min_selections,
            "maxSelections": self.max_selections,
            "displayOrder": self.display_order,
            "options": [option.as_api_payload() for option in self.options],
        }


@dataclass(frozen=True)
class AvailabilityOverride:
    override_id: UUID
    product_id: UUID
    variant_id: UUID | None
    state: str
    reason: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "overrideId": str(self.override_id),
            "productId": str(self.product_id),
            "variantId": str(self.variant_id) if self.variant_id else None,
            "state": self.state,
            "reason": self.reason,
            "startsAt": self.starts_at.isoformat() if self.starts_at else None,
            "endsAt": self.ends_at.isoformat() if self.ends_at else None,
            "createdAt": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ProductService:
    product_id: UUID
    category_id: UUID
    station_id: UUID
    name: str
    description: str | None
    enabled: bool
    variants: tuple[ProductVariant, ...]
    modifier_groups: tuple[ModifierGroup, ...]
    availability: tuple[AvailabilityOverride, ...]
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "productId": str(self.product_id),
            "categoryId": str(self.category_id),
            "stationId": str(self.station_id),
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "variants": [variant.as_api_payload() for variant in self.variants],
            "modifierGroups": [group.as_api_payload() for group in self.modifier_groups],
            "availability": [override.as_api_payload() for override in self.availability],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class MenuCategory:
    category_id: UUID
    name: str
    display_order: int
    enabled: bool
    products: tuple[ProductService, ...]
    created_at: datetime
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "categoryId": str(self.category_id),
            "name": self.name,
            "displayOrder": self.display_order,
            "enabled": self.enabled,
            "products": [product.as_api_payload() for product in self.products],
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class MenuSetupCatalog:
    categories: tuple[MenuCategory, ...]
    derived_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "categories": [category.as_api_payload() for category in self.categories],
            "derivedAt": self.derived_at.isoformat(),
        }


@dataclass(frozen=True)
class CustomerMenuVariant:
    variant_id: UUID
    name: str
    price_minor: int
    currency_code: str
    display_order: int
    is_default: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "variantId": str(self.variant_id),
            "name": self.name,
            "priceMinor": self.price_minor,
            "currencyCode": self.currency_code,
            "displayOrder": self.display_order,
            "isDefault": self.is_default,
        }


@dataclass(frozen=True)
class CustomerMenuOption:
    option_id: UUID
    name: str
    price_delta_minor: int
    currency_code: str
    display_order: int

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "optionId": str(self.option_id),
            "name": self.name,
            "priceDeltaMinor": self.price_delta_minor,
            "currencyCode": self.currency_code,
            "displayOrder": self.display_order,
        }


@dataclass(frozen=True)
class CustomerMenuModifierGroup:
    group_id: UUID
    name: str
    required: bool
    min_selections: int
    max_selections: int
    display_order: int
    options: tuple[CustomerMenuOption, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "groupId": str(self.group_id),
            "name": self.name,
            "required": self.required,
            "minSelections": self.min_selections,
            "maxSelections": self.max_selections,
            "displayOrder": self.display_order,
            "options": [option.as_api_payload() for option in self.options],
        }


@dataclass(frozen=True)
class CustomerMenuProduct:
    product_id: UUID
    category_id: UUID
    name: str
    description: str | None
    variants: tuple[CustomerMenuVariant, ...]
    modifier_groups: tuple[CustomerMenuModifierGroup, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "productId": str(self.product_id),
            "categoryId": str(self.category_id),
            "name": self.name,
            "description": self.description,
            "variants": [variant.as_api_payload() for variant in self.variants],
            "modifierGroups": [group.as_api_payload() for group in self.modifier_groups],
        }


@dataclass(frozen=True)
class CustomerMenuCategory:
    category_id: UUID
    name: str
    display_order: int
    products: tuple[CustomerMenuProduct, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "categoryId": str(self.category_id),
            "name": self.name,
            "displayOrder": self.display_order,
            "products": [product.as_api_payload() for product in self.products],
        }


@dataclass(frozen=True)
class CustomerMenu:
    categories: tuple[CustomerMenuCategory, ...]
    derived_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "categories": [category.as_api_payload() for category in self.categories],
            "derivedAt": self.derived_at.isoformat(),
        }


@dataclass(frozen=True)
class CategoryWriteCommand:
    name: str
    display_order: int


@dataclass(frozen=True)
class VariantWriteCommand:
    name: str
    price_minor: int
    currency_code: str = "TRY"
    display_order: int = 1
    is_default: bool = True
    enabled: bool = True
    variant_id: UUID | None = None


@dataclass(frozen=True)
class ProductWriteCommand:
    category_id: UUID
    station_id: UUID
    name: str
    description: str | None
    variants: tuple[VariantWriteCommand, ...]


@dataclass(frozen=True)
class ProductUpdateCommand:
    category_id: UUID | None
    station_id: UUID | None
    name: str | None
    description: str | None
    description_supplied: bool
    enabled: bool | None


@dataclass(frozen=True)
class ModifierOptionCommand:
    name: str
    price_delta_minor: int
    currency_code: str = "TRY"
    available: bool = True
    display_order: int = 1


@dataclass(frozen=True)
class ModifierGroupCommand:
    name: str
    required: bool
    min_selections: int
    max_selections: int
    display_order: int
    options: tuple[ModifierOptionCommand, ...]


@dataclass(frozen=True)
class ModifierConfigCommand:
    groups: tuple[ModifierGroupCommand, ...]


@dataclass(frozen=True)
class AvailabilityCommand:
    state: str
    reason: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    variant_id: UUID | None = None


class MenuCatalogQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_menu_setup(
        self,
        *,
        tenant_id: UUID,
        include_disabled: bool = False,
    ) -> MenuSetupCatalog:
        category_filters = [menu_categories.c.tenant_id == tenant_id]
        product_filters = [product_services.c.tenant_id == tenant_id]
        variant_filters = [product_variants.c.tenant_id == tenant_id]
        if not include_disabled:
            category_filters.append(menu_categories.c.enabled.is_(True))
            product_filters.append(product_services.c.enabled.is_(True))
            variant_filters.append(product_variants.c.enabled.is_(True))

        category_rows = (
            (
                await self.session.execute(
                    select(menu_categories)
                    .where(*category_filters)
                    .order_by(menu_categories.c.display_order, menu_categories.c.name)
                )
            )
            .mappings()
            .all()
        )
        product_rows = (
            (
                await self.session.execute(
                    select(product_services)
                    .where(*product_filters)
                    .order_by(product_services.c.name)
                )
            )
            .mappings()
            .all()
        )
        product_ids = [row["id"] for row in product_rows]
        products_by_category = await self._products_by_category(product_rows, product_ids)

        return MenuSetupCatalog(
            categories=tuple(
                category_from_row(row, tuple(products_by_category.get(row["id"], ())))
                for row in category_rows
            ),
            derived_at=utc_now(),
        )

    async def get_product_service(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        include_disabled: bool = False,
    ) -> ProductService:
        filters = [
            product_services.c.tenant_id == tenant_id,
            product_services.c.id == product_id,
        ]
        if not include_disabled:
            filters.append(product_services.c.enabled.is_(True))
        row = (
            (await self.session.execute(select(product_services).where(*filters)))
            .mappings()
            .first()
        )
        if row is None:
            raise not_found()
        return (await self._products_by_category([row], [product_id]))[row["category_id"]][0]

    async def get_customer_menu(self, *, tenant_id: UUID) -> CustomerMenu:
        setup_menu = await self.list_menu_setup(tenant_id=tenant_id, include_disabled=False)
        active_station_ids = await self._active_station_ids(tenant_id=tenant_id)
        categories = []
        for category in setup_menu.categories:
            products = tuple(
                customer_product
                for product in category.products
                if product.station_id in active_station_ids
                if (customer_product := product_to_customer_menu_product(product)) is not None
            )
            if products:
                categories.append(
                    CustomerMenuCategory(
                        category_id=category.category_id,
                        name=category.name,
                        display_order=category.display_order,
                        products=products,
                    )
                )
        return CustomerMenu(categories=tuple(categories), derived_at=utc_now())

    async def _active_station_ids(self, *, tenant_id: UUID) -> set[UUID]:
        rows = (
            (
                await self.session.execute(
                    select(stations.c.id).where(
                        stations.c.tenant_id == tenant_id,
                        stations.c.enabled.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )
        return set(rows)

    async def _products_by_category(self, product_rows, product_ids: list[UUID]):
        if not product_ids:
            return {}

        variant_rows = (
            (
                await self.session.execute(
                    select(product_variants)
                    .where(product_variants.c.product_service_id.in_(product_ids))
                    .order_by(
                        product_variants.c.product_service_id,
                        product_variants.c.display_order,
                        product_variants.c.name,
                    )
                )
            )
            .mappings()
            .all()
        )
        override_rows = (
            (
                await self.session.execute(
                    select(availability_overrides)
                    .where(availability_overrides.c.product_service_id.in_(product_ids))
                    .order_by(availability_overrides.c.created_at.desc())
                )
            )
            .mappings()
            .all()
        )
        group_rows = (
            (
                await self.session.execute(
                    select(modifier_groups)
                    .where(modifier_groups.c.product_service_id.in_(product_ids))
                    .order_by(
                        modifier_groups.c.product_service_id,
                        modifier_groups.c.display_order,
                        modifier_groups.c.name,
                    )
                )
            )
            .mappings()
            .all()
        )
        group_ids = [row["id"] for row in group_rows]
        option_rows = []
        if group_ids:
            option_rows = (
                (
                    await self.session.execute(
                        select(modifier_options)
                        .where(modifier_options.c.modifier_group_id.in_(group_ids))
                        .order_by(
                            modifier_options.c.modifier_group_id,
                            modifier_options.c.display_order,
                            modifier_options.c.name,
                        )
                    )
                )
                .mappings()
                .all()
            )

        variants_by_product: dict[UUID, list[ProductVariant]] = {}
        for row in variant_rows:
            variants_by_product.setdefault(row["product_service_id"], []).append(
                variant_from_row(row)
            )

        availability_by_product: dict[UUID, list[AvailabilityOverride]] = {}
        for row in override_rows:
            availability_by_product.setdefault(row["product_service_id"], []).append(
                availability_from_row(row)
            )

        options_by_group: dict[UUID, list[ModifierOption]] = {}
        for row in option_rows:
            options_by_group.setdefault(row["modifier_group_id"], []).append(
                modifier_option_from_row(row)
            )

        groups_by_product: dict[UUID, list[ModifierGroup]] = {}
        for row in group_rows:
            groups_by_product.setdefault(row["product_service_id"], []).append(
                modifier_group_from_row(row, tuple(options_by_group.get(row["id"], ())))
            )

        products_by_category: dict[UUID, list[ProductService]] = {}
        for row in product_rows:
            products_by_category.setdefault(row["category_id"], []).append(
                product_from_row(
                    row,
                    tuple(variants_by_product.get(row["id"], ())),
                    tuple(groups_by_product.get(row["id"], ())),
                    tuple(availability_by_product.get(row["id"], ())),
                )
            )
        return products_by_category


class MenuCatalogMutationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_category(
        self,
        *,
        actor: ActorContext,
        command: CategoryWriteCommand,
    ) -> MenuCategory:
        tenant_id = require_tenant_id(actor)
        category_id = uuid4()
        now = utc_now()
        try:
            await self.session.execute(
                insert(menu_categories).values(
                    id=category_id,
                    tenant_id=tenant_id,
                    name=command.name,
                    display_order=command.display_order,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._audit_menu(
                tenant_id=tenant_id,
                actor=actor,
                target_type="category",
                target_id=category_id,
                metadata={"operation": "category.created", "name": command.name},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_category() from exc

        return MenuCategory(
            category_id=category_id,
            name=command.name,
            display_order=command.display_order,
            enabled=True,
            products=(),
            created_at=now,
            updated_at=now,
        )

    async def update_category(
        self,
        *,
        actor: ActorContext,
        category_id: UUID,
        command: CategoryWriteCommand,
    ) -> MenuCategory:
        tenant_id = require_tenant_id(actor)
        now = utc_now()
        try:
            row = await self._update_category_row(
                tenant_id=tenant_id,
                category_id=category_id,
                values={
                    "name": command.name,
                    "display_order": command.display_order,
                    "updated_at": now,
                },
            )
            await self._audit_menu(
                tenant_id=tenant_id,
                actor=actor,
                target_type="category",
                target_id=category_id,
                metadata={"operation": "category.updated", "name": command.name},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_category() from exc
        return category_from_row(row, ())

    async def disable_category(
        self,
        *,
        actor: ActorContext,
        category_id: UUID,
        reason: str,
    ) -> MenuCategory:
        tenant_id = require_tenant_id(actor)
        now = utc_now()
        row = await self._update_category_row(
            tenant_id=tenant_id,
            category_id=category_id,
            values={"enabled": False, "updated_at": now},
        )
        await self._audit_menu(
            tenant_id=tenant_id,
            actor=actor,
            target_type="category",
            target_id=category_id,
            metadata={"operation": "category.disabled", "reason": reason},
            now=now,
        )
        await self.session.commit()
        return category_from_row(row, ())

    async def create_product_service(
        self,
        *,
        actor: ActorContext,
        command: ProductWriteCommand,
    ) -> ProductService:
        tenant_id = require_tenant_id(actor)
        if await self._load_category(tenant_id=tenant_id, category_id=command.category_id) is None:
            raise not_found()
        station = await self._load_enabled_station(
            tenant_id=tenant_id,
            station_id=command.station_id,
        )
        if station is None:
            raise station_unavailable()
        if not any(variant.enabled and variant.is_default for variant in command.variants):
            raise product_not_orderable()

        product_id = uuid4()
        now = utc_now()
        try:
            await self.session.execute(
                insert(product_services).values(
                    id=product_id,
                    tenant_id=tenant_id,
                    category_id=command.category_id,
                    station_id=command.station_id,
                    name=command.name,
                    description=command.description,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            variants = await self._insert_variants(
                tenant_id=tenant_id,
                product_id=product_id,
                commands=command.variants,
                now=now,
            )
            await self._audit_menu(
                tenant_id=tenant_id,
                actor=actor,
                target_type="product_service",
                target_id=product_id,
                metadata={
                    "operation": "product.created",
                    "categoryId": str(command.category_id),
                    "stationId": str(command.station_id),
                },
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_product() from exc

        return ProductService(
            product_id=product_id,
            category_id=command.category_id,
            station_id=command.station_id,
            name=command.name,
            description=command.description,
            enabled=True,
            variants=tuple(variants),
            modifier_groups=(),
            availability=(),
            created_at=now,
            updated_at=now,
        )

    async def update_product_service(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: ProductUpdateCommand,
    ) -> ProductService:
        tenant_id = require_tenant_id(actor)
        current = await self._load_product(tenant_id=tenant_id, product_id=product_id)
        if current is None:
            raise not_found()
        category_id = command.category_id or current["category_id"]
        station_id = command.station_id or current["station_id"]
        enabled = command.enabled if command.enabled is not None else current["enabled"]
        if await self._load_category(tenant_id=tenant_id, category_id=category_id) is None:
            raise not_found()
        if (
            enabled
            and await self._load_enabled_station(
                tenant_id=tenant_id,
                station_id=station_id,
            )
            is None
        ):
            raise station_unavailable()

        now = utc_now()
        values = {
            "category_id": category_id,
            "station_id": station_id,
            "name": command.name if command.name is not None else current["name"],
            "description": command.description
            if command.description_supplied
            else current["description"],
            "enabled": enabled,
            "updated_at": now,
        }
        try:
            await self.session.execute(
                update(product_services)
                .where(
                    product_services.c.tenant_id == tenant_id,
                    product_services.c.id == product_id,
                )
                .values(**values)
            )
            await self._audit_menu(
                tenant_id=tenant_id,
                actor=actor,
                target_type="product_service",
                target_id=product_id,
                metadata={"operation": "product.updated"},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_product() from exc
        return await MenuCatalogQueryService(self.session).get_product_service(
            tenant_id=tenant_id,
            product_id=product_id,
            include_disabled=True,
        )

    async def disable_product_service(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        reason: str,
    ) -> ProductService:
        return await self.update_product_service(
            actor=actor,
            product_id=product_id,
            command=ProductUpdateCommand(
                category_id=None,
                station_id=None,
                name=None,
                description=None,
                description_supplied=False,
                enabled=False,
            ),
        )

    async def manage_variant(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: VariantWriteCommand,
    ) -> ProductVariant:
        tenant_id = require_tenant_id(actor)
        if await self._load_product(tenant_id=tenant_id, product_id=product_id) is None:
            raise not_found()
        if command.variant_id and not await self._load_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            variant_id=command.variant_id,
        ):
            raise not_found()
        now = utc_now()
        variant_id = command.variant_id or uuid4()
        try:
            if command.is_default:
                await self.session.execute(
                    update(product_variants)
                    .where(
                        product_variants.c.tenant_id == tenant_id,
                        product_variants.c.product_service_id == product_id,
                    )
                    .values(is_default=False, updated_at=now)
                )
            values = {
                "name": command.name,
                "price_minor": command.price_minor,
                "currency_code": command.currency_code,
                "display_order": command.display_order,
                "is_default": command.is_default,
                "enabled": command.enabled,
                "updated_at": now,
            }
            if command.variant_id:
                result = await self.session.execute(
                    update(product_variants)
                    .where(
                        product_variants.c.tenant_id == tenant_id,
                        product_variants.c.product_service_id == product_id,
                        product_variants.c.id == command.variant_id,
                    )
                    .values(**values)
                    .returning(product_variants)
                )
                row = result.mappings().first()
                if row is None:
                    raise not_found()
            else:
                await self.session.execute(
                    insert(product_variants).values(
                        id=variant_id,
                        tenant_id=tenant_id,
                        product_service_id=product_id,
                        created_at=now,
                        **values,
                    )
                )
            if not await self._has_enabled_default_variant(
                tenant_id=tenant_id,
                product_id=product_id,
            ):
                raise product_not_orderable()
            await self._audit_menu(
                tenant_id=tenant_id,
                actor=actor,
                target_type="product_variant",
                target_id=variant_id,
                metadata={"operation": "variant.managed", "productId": str(product_id)},
                now=now,
            )
            await self.session.commit()
        except ApiError:
            await self.session.rollback()
            raise
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_product() from exc
        return ProductVariant(
            variant_id=variant_id,
            product_id=product_id,
            name=command.name,
            price_minor=command.price_minor,
            currency_code=command.currency_code,
            display_order=command.display_order,
            is_default=command.is_default,
            enabled=command.enabled,
        )

    async def manage_modifiers(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: ModifierConfigCommand,
    ) -> tuple[ModifierGroup, ...]:
        tenant_id = require_tenant_id(actor)
        if await self._load_product(tenant_id=tenant_id, product_id=product_id) is None:
            raise not_found()
        validate_modifier_config(command)
        now = utc_now()
        try:
            existing_groups = (
                (
                    await self.session.execute(
                        select(modifier_groups.c.id).where(
                            modifier_groups.c.tenant_id == tenant_id,
                            modifier_groups.c.product_service_id == product_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            if existing_groups:
                await self.session.execute(
                    delete(modifier_options).where(
                        modifier_options.c.tenant_id == tenant_id,
                        modifier_options.c.modifier_group_id.in_(existing_groups),
                    )
                )
                await self.session.execute(
                    delete(modifier_groups).where(
                        modifier_groups.c.tenant_id == tenant_id,
                        modifier_groups.c.id.in_(existing_groups),
                    )
                )
            groups = await self._insert_modifier_groups(
                tenant_id=tenant_id,
                product_id=product_id,
                command=command,
                now=now,
            )
            await self._audit_menu(
                tenant_id=tenant_id,
                actor=actor,
                target_type="product_service",
                target_id=product_id,
                metadata={"operation": "modifiers.replaced"},
                now=now,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise duplicate_product() from exc
        return tuple(groups)

    async def set_availability(
        self,
        *,
        actor: ActorContext,
        product_id: UUID,
        command: AvailabilityCommand,
    ) -> AvailabilityOverride:
        tenant_id = require_tenant_id(actor)
        if actor.user_id is None:
            raise not_authorized()
        if command.state not in {"available", "unavailable"}:
            raise validation_failed("availability state is invalid")
        if command.ends_at and command.starts_at and command.ends_at <= command.starts_at:
            raise validation_failed("availability window is invalid")
        if await self._load_product(tenant_id=tenant_id, product_id=product_id) is None:
            raise not_found()
        if command.variant_id and not await self._load_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            variant_id=command.variant_id,
        ):
            raise variant_invalid()

        now = utc_now()
        override_id = uuid4()
        await self.session.execute(
            insert(availability_overrides).values(
                id=override_id,
                tenant_id=tenant_id,
                product_service_id=product_id,
                product_variant_id=command.variant_id,
                state=command.state,
                reason=command.reason,
                starts_at=command.starts_at,
                expires_at=command.ends_at,
                created_by_user_id=actor.user_id,
                created_at=now,
            )
        )
        await self._audit_availability(
            tenant_id=tenant_id,
            actor=actor,
            target_type="product_service",
            target_id=product_id,
            metadata={"operation": "availability.set", "state": command.state},
            now=now,
        )
        await self.session.commit()
        return AvailabilityOverride(
            override_id=override_id,
            product_id=product_id,
            variant_id=command.variant_id,
            state=command.state,
            reason=command.reason,
            starts_at=command.starts_at,
            ends_at=command.ends_at,
            created_at=now,
        )

    async def _update_category_row(
        self,
        *,
        tenant_id: UUID,
        category_id: UUID,
        values: dict[str, object],
    ):
        result = await self.session.execute(
            update(menu_categories)
            .where(
                menu_categories.c.tenant_id == tenant_id,
                menu_categories.c.id == category_id,
            )
            .values(**values)
            .returning(menu_categories)
        )
        row = result.mappings().first()
        if row is None:
            raise not_found()
        return row

    async def _insert_variants(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        commands: tuple[VariantWriteCommand, ...],
        now: datetime,
    ) -> list[ProductVariant]:
        variants = []
        for variant in commands:
            variant_id = uuid4()
            await self.session.execute(
                insert(product_variants).values(
                    id=variant_id,
                    tenant_id=tenant_id,
                    product_service_id=product_id,
                    name=variant.name,
                    price_minor=variant.price_minor,
                    currency_code=variant.currency_code,
                    display_order=variant.display_order,
                    is_default=variant.is_default,
                    enabled=variant.enabled,
                    created_at=now,
                    updated_at=now,
                )
            )
            variants.append(
                ProductVariant(
                    variant_id=variant_id,
                    product_id=product_id,
                    name=variant.name,
                    price_minor=variant.price_minor,
                    currency_code=variant.currency_code,
                    display_order=variant.display_order,
                    is_default=variant.is_default,
                    enabled=variant.enabled,
                )
            )
        return variants

    async def _insert_modifier_groups(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        command: ModifierConfigCommand,
        now: datetime,
    ) -> list[ModifierGroup]:
        groups = []
        for group_command in command.groups:
            group_id = uuid4()
            await self.session.execute(
                insert(modifier_groups).values(
                    id=group_id,
                    tenant_id=tenant_id,
                    product_service_id=product_id,
                    name=group_command.name,
                    required=group_command.required,
                    min_selections=group_command.min_selections,
                    max_selections=group_command.max_selections,
                    display_order=group_command.display_order,
                    created_at=now,
                    updated_at=now,
                )
            )
            options = []
            for option_command in group_command.options:
                option_id = uuid4()
                await self.session.execute(
                    insert(modifier_options).values(
                        id=option_id,
                        tenant_id=tenant_id,
                        modifier_group_id=group_id,
                        name=option_command.name,
                        price_delta_minor=option_command.price_delta_minor,
                        currency_code=option_command.currency_code,
                        available=option_command.available,
                        display_order=option_command.display_order,
                        created_at=now,
                        updated_at=now,
                    )
                )
                options.append(
                    ModifierOption(
                        option_id=option_id,
                        group_id=group_id,
                        name=option_command.name,
                        price_delta_minor=option_command.price_delta_minor,
                        currency_code=option_command.currency_code,
                        available=option_command.available,
                        display_order=option_command.display_order,
                    )
                )
            groups.append(
                ModifierGroup(
                    group_id=group_id,
                    product_id=product_id,
                    name=group_command.name,
                    required=group_command.required,
                    min_selections=group_command.min_selections,
                    max_selections=group_command.max_selections,
                    display_order=group_command.display_order,
                    options=tuple(options),
                )
            )
        return groups

    async def _load_category(self, *, tenant_id: UUID, category_id: UUID):
        return (
            (
                await self.session.execute(
                    select(menu_categories).where(
                        menu_categories.c.tenant_id == tenant_id,
                        menu_categories.c.id == category_id,
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _load_product(self, *, tenant_id: UUID, product_id: UUID):
        return (
            (
                await self.session.execute(
                    select(product_services).where(
                        product_services.c.tenant_id == tenant_id,
                        product_services.c.id == product_id,
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _load_variant(self, *, tenant_id: UUID, product_id: UUID, variant_id: UUID):
        return (
            (
                await self.session.execute(
                    select(product_variants).where(
                        product_variants.c.tenant_id == tenant_id,
                        product_variants.c.product_service_id == product_id,
                        product_variants.c.id == variant_id,
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _load_enabled_station(self, *, tenant_id: UUID, station_id: UUID):
        return (
            (
                await self.session.execute(
                    select(stations).where(
                        stations.c.tenant_id == tenant_id,
                        stations.c.id == station_id,
                        stations.c.enabled.is_(True),
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _has_enabled_default_variant(self, *, tenant_id: UUID, product_id: UUID) -> bool:
        row = (
            (
                await self.session.execute(
                    select(product_variants.c.id).where(
                        product_variants.c.tenant_id == tenant_id,
                        product_variants.c.product_service_id == product_id,
                        product_variants.c.enabled.is_(True),
                        product_variants.c.is_default.is_(True),
                    )
                )
            )
            .mappings()
            .first()
        )
        return row is not None

    async def _audit_menu(
        self,
        *,
        tenant_id: UUID,
        actor: ActorContext,
        target_type: str,
        target_id: UUID,
        metadata: dict[str, object],
        now: datetime,
    ) -> None:
        await self._audit(
            tenant_id=tenant_id,
            actor=actor,
            action="menu_catalog.changed",
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            now=now,
        )

    async def _audit_availability(
        self,
        *,
        tenant_id: UUID,
        actor: ActorContext,
        target_type: str,
        target_id: UUID,
        metadata: dict[str, object],
        now: datetime,
    ) -> None:
        await self._audit(
            tenant_id=tenant_id,
            actor=actor,
            action="availability.changed",
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            now=now,
        )

    async def _audit(
        self,
        *,
        tenant_id: UUID,
        actor: ActorContext,
        action: str,
        target_type: str,
        target_id: UUID,
        metadata: dict[str, object],
        now: datetime,
    ) -> None:
        await self.session.execute(
            insert(audit_events).values(
                id=uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor.user_id,
                action=action,
                target_type=target_type,
                target_id=str(target_id),
                metadata=metadata,
                created_at=now,
            )
        )


def category_from_row(row, products: tuple[ProductService, ...]) -> MenuCategory:
    return MenuCategory(
        category_id=row["id"],
        name=row["name"],
        display_order=row["display_order"],
        enabled=row["enabled"],
        products=products,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def product_from_row(
    row,
    variants: tuple[ProductVariant, ...],
    groups: tuple[ModifierGroup, ...],
    availability: tuple[AvailabilityOverride, ...],
) -> ProductService:
    return ProductService(
        product_id=row["id"],
        category_id=row["category_id"],
        station_id=row["station_id"],
        name=row["name"],
        description=row["description"],
        enabled=row["enabled"],
        variants=variants,
        modifier_groups=groups,
        availability=availability,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def variant_from_row(row) -> ProductVariant:
    return ProductVariant(
        variant_id=row["id"],
        product_id=row["product_service_id"],
        name=row["name"],
        price_minor=row["price_minor"],
        currency_code=row["currency_code"],
        display_order=row["display_order"],
        is_default=row["is_default"],
        enabled=row["enabled"],
    )


def modifier_group_from_row(row, options: tuple[ModifierOption, ...]) -> ModifierGroup:
    return ModifierGroup(
        group_id=row["id"],
        product_id=row["product_service_id"],
        name=row["name"],
        required=row["required"],
        min_selections=row["min_selections"],
        max_selections=row["max_selections"],
        display_order=row["display_order"],
        options=options,
    )


def modifier_option_from_row(row) -> ModifierOption:
    return ModifierOption(
        option_id=row["id"],
        group_id=row["modifier_group_id"],
        name=row["name"],
        price_delta_minor=row["price_delta_minor"],
        currency_code=row["currency_code"],
        available=row["available"],
        display_order=row["display_order"],
    )


def availability_from_row(row) -> AvailabilityOverride:
    return AvailabilityOverride(
        override_id=row["id"],
        product_id=row["product_service_id"],
        variant_id=row["product_variant_id"],
        state=row["state"],
        reason=row["reason"],
        starts_at=row["starts_at"],
        ends_at=row["expires_at"],
        created_at=row["created_at"],
    )


def product_to_customer_menu_product(product: ProductService) -> CustomerMenuProduct | None:
    now = utc_now()
    product_unavailable = latest_active_availability_state(
        product.availability,
        variant_id=None,
        now=now,
    )
    if product_unavailable == "unavailable":
        return None

    variants = tuple(
        CustomerMenuVariant(
            variant_id=variant.variant_id,
            name=variant.name,
            price_minor=variant.price_minor,
            currency_code=variant.currency_code,
            display_order=variant.display_order,
            is_default=variant.is_default,
        )
        for variant in product.variants
        if variant.enabled
        and latest_active_availability_state(
            product.availability,
            variant_id=variant.variant_id,
            now=now,
        )
        != "unavailable"
    )
    if not variants or not any(variant.is_default for variant in variants):
        return None

    modifier_groups = tuple(
        CustomerMenuModifierGroup(
            group_id=group.group_id,
            name=group.name,
            required=group.required,
            min_selections=group.min_selections,
            max_selections=group.max_selections,
            display_order=group.display_order,
            options=tuple(
                CustomerMenuOption(
                    option_id=option.option_id,
                    name=option.name,
                    price_delta_minor=option.price_delta_minor,
                    currency_code=option.currency_code,
                    display_order=option.display_order,
                )
                for option in group.options
                if option.available
            ),
        )
        for group in product.modifier_groups
    )
    if any(
        group.required and len(group.options) < group.min_selections for group in modifier_groups
    ):
        return None

    return CustomerMenuProduct(
        product_id=product.product_id,
        category_id=product.category_id,
        name=product.name,
        description=product.description,
        variants=variants,
        modifier_groups=modifier_groups,
    )


def latest_active_availability_state(
    overrides: tuple[AvailabilityOverride, ...],
    *,
    variant_id: UUID | None,
    now: datetime,
) -> str | None:
    scoped_overrides = [
        override
        for override in overrides
        if override.variant_id == variant_id
        and (override.starts_at is None or override.starts_at <= now)
        and (override.ends_at is None or override.ends_at > now)
    ]
    if not scoped_overrides:
        return None
    return max(scoped_overrides, key=lambda override: override.created_at).state


def validate_modifier_config(command: ModifierConfigCommand) -> None:
    for group in command.groups:
        if group.min_selections > group.max_selections:
            raise validation_failed("modifier selection bounds are invalid")
        if group.required and group.min_selections < 1:
            raise validation_failed("required modifier group must require at least one selection")
        if group.max_selections > len(group.options):
            raise validation_failed("modifier max selections exceeds available options")


def require_tenant_id(actor: ActorContext) -> UUID:
    if actor.tenant_id is None:
        raise not_authorized()
    return actor.tenant_id


def utc_now() -> datetime:
    return datetime.now(UTC)


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def not_found() -> ApiError:
    return ApiError(status_code=404, code="not_found_or_hidden", message="Not found.")


def validation_failed(message: str) -> ApiError:
    return ApiError(status_code=422, code="validation_failed", message=message)


def duplicate_category() -> ApiError:
    return ApiError(
        status_code=409,
        code="duplicate_category",
        message="Category name or display order already exists.",
    )


def duplicate_product() -> ApiError:
    return ApiError(
        status_code=409,
        code="duplicate_product",
        message="Product, variant, or modifier name already exists.",
    )


def product_not_orderable() -> ApiError:
    return ApiError(
        status_code=422,
        code="product_not_orderable",
        message="Product needs an enabled default variant.",
    )


def station_unavailable() -> ApiError:
    return ApiError(
        status_code=422,
        code="station_unavailable",
        message="Station is unavailable.",
    )


def variant_invalid() -> ApiError:
    return ApiError(
        status_code=422,
        code="variant_invalid",
        message="Variant does not belong to product.",
    )
