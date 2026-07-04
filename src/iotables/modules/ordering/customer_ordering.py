import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import (
    checks,
    customer_cart_items,
    customer_carts,
    customer_ordering_sessions,
    order_items,
    order_submit_idempotency,
    orders,
    preparation_items,
    preparation_transitions,
    table_sessions,
)
from iotables.modules.ordering.table_presence import hash_customer_session_token
from iotables.modules.tenant_setup.menu_catalog import (
    MenuCatalogQueryService,
    ProductService,
    product_to_customer_menu_product,
)
from iotables.security.context import ActorContext, StaffRole


@dataclass(frozen=True)
class CartItemWriteCommand:
    client_cart_item_id: str
    product_id: UUID
    variant_id: UUID
    modifier_option_ids: tuple[UUID, ...]
    quantity: int
    note: str | None


@dataclass(frozen=True)
class CustomerCartItem:
    client_cart_item_id: str
    product_id: UUID
    variant_id: UUID
    quantity: int
    selected_modifiers: tuple[UUID, ...]
    note: str | None
    estimated_price_minor: int

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "clientCartItemId": self.client_cart_item_id,
            "productId": str(self.product_id),
            "variantId": str(self.variant_id),
            "quantity": self.quantity,
            "modifierOptionIds": [str(option_id) for option_id in self.selected_modifiers],
            "note": self.note,
            "estimatedPriceMinor": self.estimated_price_minor,
        }


@dataclass(frozen=True)
class CustomerCart:
    cart_id: UUID
    version: str
    items: tuple[CustomerCartItem, ...]
    display_subtotal_minor: int
    currency: str
    updated_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "cartId": str(self.cart_id),
            "version": self.version,
            "items": [item.as_api_payload() for item in self.items],
            "displaySubtotalMinor": self.display_subtotal_minor,
            "currency": self.currency,
            "updatedAt": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class SubmitOrderCommand:
    cart_version: str
    cart_item_ids: tuple[str, ...]


@dataclass(frozen=True)
class SubmittedOrderItem:
    order_item_id: UUID
    product_id: UUID
    variant_id: UUID
    station_id: UUID
    name: str
    variant_name: str
    quantity: int
    unit_price_minor: int
    note: str | None

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "orderItemId": str(self.order_item_id),
            "productId": str(self.product_id),
            "variantId": str(self.variant_id),
            "stationId": str(self.station_id),
            "name": self.name,
            "variantName": self.variant_name,
            "quantity": self.quantity,
            "unitPriceMinor": self.unit_price_minor,
            "note": self.note,
        }


@dataclass(frozen=True)
class SubmittedOrderResult:
    order_id: UUID
    table_session_id: UUID
    check_id: UUID
    items: tuple[SubmittedOrderItem, ...]
    cart_cleared: bool
    duplicate: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "orderId": str(self.order_id),
            "tableSessionId": str(self.table_session_id),
            "checkId": str(self.check_id),
            "items": [item.as_api_payload() for item in self.items],
            "cartCleared": self.cart_cleared,
            "duplicate": self.duplicate,
        }


@dataclass(frozen=True)
class CashierOrderItem:
    order_item_id: UUID
    name: str
    variant_name: str
    quantity: int
    unit_price_minor: int
    currency: str
    note: str | None
    voided: bool

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "orderItemId": str(self.order_item_id),
            "name": self.name,
            "variantName": self.variant_name,
            "quantity": self.quantity,
            "unitPriceMinor": self.unit_price_minor,
            "currency": self.currency,
            "note": self.note,
            "voided": self.voided,
        }


@dataclass(frozen=True)
class CashierOrder:
    order_id: UUID
    table_session_id: UUID
    submitted_at: datetime
    items: tuple[CashierOrderItem, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "orderId": str(self.order_id),
            "tableSessionId": str(self.table_session_id),
            "submittedAt": self.submitted_at.isoformat(),
            "items": [item.as_api_payload() for item in self.items],
        }


@dataclass(frozen=True)
class CashierOrderList:
    items: tuple[CashierOrder, ...]

    def as_api_payload(self) -> dict[str, Any]:
        return {"items": [item.as_api_payload() for item in self.items]}


class CustomerOrderingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_cart(self, *, customer_session_token: str | None) -> CustomerCart:
        session_row = await self._load_customer_session(customer_session_token)
        cart_row = await self._get_or_create_active_cart(session_row)
        return await self._cart_from_row(cart_row)

    async def add_or_update_cart_item(
        self,
        *,
        customer_session_token: str | None,
        command: CartItemWriteCommand,
    ) -> CustomerCart:
        if command.quantity <= 0:
            raise validation_failed("quantity must be positive")
        session_row = await self._load_customer_session(customer_session_token)
        cart_row = await self._get_or_create_active_cart(session_row)
        product = await MenuCatalogQueryService(self.session).get_product_service(
            tenant_id=session_row["tenant_id"],
            product_id=command.product_id,
            include_disabled=False,
        )
        unit_price = validate_and_price_cart_item(product=product, command=command)
        now = utc_now()
        statement = (
            pg_insert(customer_cart_items)
            .values(
                id=uuid4(),
                tenant_id=session_row["tenant_id"],
                cart_id=cart_row["id"],
                client_cart_item_id=command.client_cart_item_id,
                product_service_id=command.product_id,
                product_variant_id=command.variant_id,
                quantity=command.quantity,
                selected_modifiers=[str(option_id) for option_id in command.modifier_option_ids],
                note=command.note,
                estimated_price_minor=unit_price * command.quantity,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_customer_cart_items__tenant_cart_client_item",
                set_={
                    "product_service_id": command.product_id,
                    "product_variant_id": command.variant_id,
                    "quantity": command.quantity,
                    "selected_modifiers": [
                        str(option_id) for option_id in command.modifier_option_ids
                    ],
                    "note": command.note,
                    "estimated_price_minor": unit_price * command.quantity,
                    "updated_at": now,
                },
            )
        )
        await self.session.execute(statement)
        await self.session.execute(
            update(customer_carts)
            .where(customer_carts.c.id == cart_row["id"])
            .values(updated_at=now)
        )
        await self.session.commit()
        return await self._cart_from_row(cart_row)

    async def remove_cart_item(
        self,
        *,
        customer_session_token: str | None,
        client_cart_item_id: str,
    ) -> CustomerCart:
        session_row = await self._load_customer_session(customer_session_token)
        cart_row = await self._get_or_create_active_cart(session_row)
        now = utc_now()
        await self.session.execute(
            delete(customer_cart_items).where(
                customer_cart_items.c.tenant_id == session_row["tenant_id"],
                customer_cart_items.c.cart_id == cart_row["id"],
                customer_cart_items.c.client_cart_item_id == client_cart_item_id,
            )
        )
        await self.session.execute(
            update(customer_carts)
            .where(customer_carts.c.id == cart_row["id"])
            .values(updated_at=now)
        )
        await self.session.commit()
        return await self._cart_from_row(cart_row)

    async def submit_order(
        self,
        *,
        customer_session_token: str | None,
        idempotency_key: str,
        command: SubmitOrderCommand,
    ) -> SubmittedOrderResult:
        session_row = await self._load_customer_session(customer_session_token)
        now = utc_now()
        if session_row["presence_valid_until"] <= now:
            raise fresh_presence_required()
        cart_row = await self._load_active_cart(session_row)
        if cart_row is None:
            raise empty_cart()
        cart_items = await self._cart_item_rows(cart_row)
        if command.cart_item_ids:
            selected_ids = set(command.cart_item_ids)
            cart_items = [row for row in cart_items if row["client_cart_item_id"] in selected_ids]
        if not cart_items:
            raise empty_cart()

        request_hash = hash_submit_request(command=command, cart_items=cart_items)
        existing_idempotency = await self._load_submit_idempotency(
            tenant_id=session_row["tenant_id"],
            customer_ordering_session_id=session_row["id"],
            idempotency_key=idempotency_key,
        )
        if existing_idempotency is not None:
            if existing_idempotency["request_hash"] != request_hash:
                raise idempotency_conflict()
            if existing_idempotency["status"] == "completed" and existing_idempotency["order_id"]:
                return await self._submitted_order_result(
                    tenant_id=session_row["tenant_id"],
                    order_id=existing_idempotency["order_id"],
                    duplicate=True,
                )

        if existing_idempotency is None:
            await self.session.execute(
                insert(order_submit_idempotency).values(
                    id=uuid4(),
                    tenant_id=session_row["tenant_id"],
                    customer_ordering_session_id=session_row["id"],
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    order_id=None,
                    status="processing",
                    created_at=now,
                    completed_at=None,
                )
            )

        table_session_id, check_id = await self._open_table_session_and_check(session_row, now)
        order_id = uuid4()
        await self.session.execute(
            insert(orders).values(
                id=order_id,
                tenant_id=session_row["tenant_id"],
                customer_ordering_session_id=session_row["id"],
                table_session_id=table_session_id,
                status="submitted",
                order_channel="dine_in_qr",
                submitted_at=now,
                created_at=now,
            )
        )

        submitted_items = []
        for row in cart_items:
            product = await MenuCatalogQueryService(self.session).get_product_service(
                tenant_id=session_row["tenant_id"],
                product_id=row["product_service_id"],
                include_disabled=False,
            )
            cart_command = CartItemWriteCommand(
                client_cart_item_id=row["client_cart_item_id"],
                product_id=row["product_service_id"],
                variant_id=row["product_variant_id"],
                modifier_option_ids=tuple(UUID(value) for value in row["selected_modifiers"]),
                quantity=row["quantity"],
                note=row["note"],
            )
            unit_price = validate_and_price_cart_item(product=product, command=cart_command)
            variant = next(
                variant
                for variant in product.variants
                if variant.variant_id == row["product_variant_id"]
            )
            order_item_id = uuid4()
            await self.session.execute(
                insert(order_items).values(
                    id=order_item_id,
                    tenant_id=session_row["tenant_id"],
                    order_id=order_id,
                    product_service_id=product.product_id,
                    product_variant_id=variant.variant_id,
                    station_id=product.station_id,
                    name_snapshot=product.name,
                    variant_name_snapshot=variant.name,
                    unit_price_minor=unit_price,
                    currency_code=variant.currency_code,
                    modifier_snapshot=row["selected_modifiers"],
                    quantity=row["quantity"],
                    note=row["note"],
                    voided_at=None,
                    voided_by_user_id=None,
                    void_reason=None,
                    created_at=now,
                )
            )
            preparation_item_id = uuid4()
            await self.session.execute(
                insert(preparation_items).values(
                    id=preparation_item_id,
                    tenant_id=session_row["tenant_id"],
                    order_item_id=order_item_id,
                    station_id=product.station_id,
                    status="pending",
                    cannot_prepare_reason=None,
                    updated_by_user_id=None,
                    updated_at=now,
                    created_at=now,
                )
            )
            await self.session.execute(
                insert(preparation_transitions).values(
                    id=uuid4(),
                    tenant_id=session_row["tenant_id"],
                    preparation_item_id=preparation_item_id,
                    actor_user_id=None,
                    from_status=None,
                    to_status="pending",
                    reason=None,
                    created_at=now,
                )
            )
            submitted_items.append(
                SubmittedOrderItem(
                    order_item_id=order_item_id,
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    station_id=product.station_id,
                    name=product.name,
                    variant_name=variant.name,
                    quantity=row["quantity"],
                    unit_price_minor=unit_price,
                    note=row["note"],
                )
            )

        await self.session.execute(
            update(customer_carts)
            .where(customer_carts.c.id == cart_row["id"])
            .values(status="submitted", updated_at=now)
        )
        await self.session.execute(
            update(customer_ordering_sessions)
            .where(customer_ordering_sessions.c.id == session_row["id"])
            .values(table_session_id=table_session_id, last_seen_at=now, updated_at=now)
        )
        await self.session.execute(
            update(order_submit_idempotency)
            .where(
                order_submit_idempotency.c.tenant_id == session_row["tenant_id"],
                order_submit_idempotency.c.customer_ordering_session_id == session_row["id"],
                order_submit_idempotency.c.idempotency_key == idempotency_key,
            )
            .values(order_id=order_id, status="completed", completed_at=now)
        )
        await self.session.commit()
        return SubmittedOrderResult(
            order_id=order_id,
            table_session_id=table_session_id,
            check_id=check_id,
            items=tuple(submitted_items),
            cart_cleared=True,
            duplicate=False,
        )

    async def list_table_orders(
        self,
        *,
        actor: ActorContext,
        table_session_id: UUID,
    ) -> CashierOrderList:
        if actor.tenant_id is None or StaffRole.CASHIER not in actor.roles or actor.user_id is None:
            raise not_authorized()
        session_exists = (
            await self.session.execute(
                select(table_sessions.c.id).where(
                    table_sessions.c.tenant_id == actor.tenant_id,
                    table_sessions.c.id == table_session_id,
                )
            )
        ).scalar_one_or_none()
        if session_exists is None:
            raise not_found_or_hidden()
        order_rows = (
            (
                await self.session.execute(
                    select(orders).where(
                        orders.c.tenant_id == actor.tenant_id,
                        orders.c.table_session_id == table_session_id,
                    )
                )
            )
            .mappings()
            .all()
        )
        result = []
        for order_row in order_rows:
            item_rows = (
                (
                    await self.session.execute(
                        select(order_items)
                        .where(
                            order_items.c.tenant_id == actor.tenant_id,
                            order_items.c.order_id == order_row["id"],
                        )
                        .order_by(order_items.c.created_at)
                    )
                )
                .mappings()
                .all()
            )
            result.append(
                CashierOrder(
                    order_id=order_row["id"],
                    table_session_id=order_row["table_session_id"],
                    submitted_at=order_row["submitted_at"],
                    items=tuple(
                        CashierOrderItem(
                            order_item_id=row["id"],
                            name=row["name_snapshot"],
                            variant_name=row["variant_name_snapshot"],
                            quantity=row["quantity"],
                            unit_price_minor=row["unit_price_minor"],
                            currency=row["currency_code"],
                            note=row["note"],
                            voided=row["voided_at"] is not None,
                        )
                        for row in item_rows
                    ),
                )
            )
        return CashierOrderList(items=tuple(result))

    async def _load_customer_session(self, customer_session_token: str | None):
        if not customer_session_token:
            raise session_expired()
        now = utc_now()
        row = (
            (
                await self.session.execute(
                    select(customer_ordering_sessions).where(
                        customer_ordering_sessions.c.cookie_token_hash
                        == hash_customer_session_token(customer_session_token),
                        customer_ordering_sessions.c.expires_at > now,
                    )
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise session_expired()
        return row

    async def _get_or_create_active_cart(self, session_row):
        row = (
            (
                await self.session.execute(
                    select(customer_carts).where(
                        customer_carts.c.tenant_id == session_row["tenant_id"],
                        customer_carts.c.customer_ordering_session_id == session_row["id"],
                        customer_carts.c.status == "active",
                    )
                )
            )
            .mappings()
            .first()
        )
        if row is not None:
            return row
        now = utc_now()
        cart_id = uuid4()
        await self.session.execute(
            insert(customer_carts).values(
                id=cart_id,
                tenant_id=session_row["tenant_id"],
                customer_ordering_session_id=session_row["id"],
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        await self.session.commit()
        return (
            (
                await self.session.execute(
                    select(customer_carts).where(customer_carts.c.id == cart_id)
                )
            )
            .mappings()
            .one()
        )

    async def _load_active_cart(self, session_row):
        return (
            (
                await self.session.execute(
                    select(customer_carts).where(
                        customer_carts.c.tenant_id == session_row["tenant_id"],
                        customer_carts.c.customer_ordering_session_id == session_row["id"],
                        customer_carts.c.status == "active",
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _cart_item_rows(self, cart_row):
        return (
            (
                await self.session.execute(
                    select(customer_cart_items)
                    .where(
                        customer_cart_items.c.tenant_id == cart_row["tenant_id"],
                        customer_cart_items.c.cart_id == cart_row["id"],
                    )
                    .order_by(customer_cart_items.c.created_at)
                )
            )
            .mappings()
            .all()
        )

    async def _open_table_session_and_check(self, session_row, now: datetime) -> tuple[UUID, UUID]:
        current = (
            (
                await self.session.execute(
                    select(table_sessions).where(
                        table_sessions.c.tenant_id == session_row["tenant_id"],
                        table_sessions.c.table_id == session_row["table_id"],
                        table_sessions.c.status == "open",
                    )
                )
            )
            .mappings()
            .first()
        )
        if current is None:
            table_session_id = uuid4()
            try:
                await self.session.execute(
                    insert(table_sessions).values(
                        id=table_session_id,
                        tenant_id=session_row["tenant_id"],
                        table_id=session_row["table_id"],
                        status="open",
                        opened_at=now,
                        closed_at=None,
                        created_at=now,
                        updated_at=now,
                    )
                )
            except IntegrityError:
                await self.session.rollback()
                raise closed_table_session() from None
        else:
            table_session_id = current["id"]

        check_row = (
            (
                await self.session.execute(
                    select(checks).where(checks.c.table_session_id == table_session_id)
                )
            )
            .mappings()
            .first()
        )
        if check_row is not None:
            return table_session_id, check_row["id"]

        check_id = uuid4()
        await self.session.execute(
            insert(checks).values(
                id=check_id,
                tenant_id=session_row["tenant_id"],
                table_session_id=table_session_id,
                status="open",
                opened_at=now,
                closed_at=None,
            )
        )
        return table_session_id, check_id

    async def _load_submit_idempotency(
        self,
        *,
        tenant_id: UUID,
        customer_ordering_session_id: UUID,
        idempotency_key: str,
    ):
        return (
            (
                await self.session.execute(
                    select(order_submit_idempotency).where(
                        order_submit_idempotency.c.tenant_id == tenant_id,
                        order_submit_idempotency.c.customer_ordering_session_id
                        == customer_ordering_session_id,
                        order_submit_idempotency.c.idempotency_key == idempotency_key,
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _submitted_order_result(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        duplicate: bool,
    ) -> SubmittedOrderResult:
        order_row = (
            (
                await self.session.execute(
                    select(orders).where(
                        orders.c.tenant_id == tenant_id,
                        orders.c.id == order_id,
                    )
                )
            )
            .mappings()
            .one()
        )
        check_row = (
            (
                await self.session.execute(
                    select(checks).where(checks.c.table_session_id == order_row["table_session_id"])
                )
            )
            .mappings()
            .one()
        )
        item_rows = (
            (
                await self.session.execute(
                    select(order_items)
                    .where(order_items.c.tenant_id == tenant_id, order_items.c.order_id == order_id)
                    .order_by(order_items.c.created_at)
                )
            )
            .mappings()
            .all()
        )
        return SubmittedOrderResult(
            order_id=order_id,
            table_session_id=order_row["table_session_id"],
            check_id=check_row["id"],
            items=tuple(
                SubmittedOrderItem(
                    order_item_id=row["id"],
                    product_id=row["product_service_id"],
                    variant_id=row["product_variant_id"],
                    station_id=row["station_id"],
                    name=row["name_snapshot"],
                    variant_name=row["variant_name_snapshot"],
                    quantity=row["quantity"],
                    unit_price_minor=row["unit_price_minor"],
                    note=row["note"],
                )
                for row in item_rows
            ),
            cart_cleared=True,
            duplicate=duplicate,
        )

    async def _cart_from_row(self, cart_row) -> CustomerCart:
        rows = (
            (
                await self.session.execute(
                    select(customer_cart_items)
                    .where(
                        customer_cart_items.c.tenant_id == cart_row["tenant_id"],
                        customer_cart_items.c.cart_id == cart_row["id"],
                    )
                    .order_by(customer_cart_items.c.created_at)
                )
            )
            .mappings()
            .all()
        )
        items = tuple(
            CustomerCartItem(
                client_cart_item_id=row["client_cart_item_id"],
                product_id=row["product_service_id"],
                variant_id=row["product_variant_id"],
                quantity=row["quantity"],
                selected_modifiers=tuple(UUID(value) for value in row["selected_modifiers"]),
                note=row["note"],
                estimated_price_minor=row["estimated_price_minor"],
            )
            for row in rows
        )
        subtotal = sum(item.estimated_price_minor for item in items)
        return CustomerCart(
            cart_id=cart_row["id"],
            version=str(cart_row["updated_at"].timestamp()),
            items=items,
            display_subtotal_minor=subtotal,
            currency="TRY",
            updated_at=cart_row["updated_at"],
        )


def validate_and_price_cart_item(*, product: ProductService, command: CartItemWriteCommand) -> int:
    customer_product = product_to_customer_menu_product(product)
    if customer_product is None:
        raise item_not_orderable()
    variant = next(
        (
            variant
            for variant in customer_product.variants
            if variant.variant_id == command.variant_id
        ),
        None,
    )
    if variant is None:
        raise variant_invalid()

    selected = set(command.modifier_option_ids)
    option_prices: dict[UUID, int] = {}
    for group in customer_product.modifier_groups:
        group_option_ids = {option.option_id for option in group.options}
        selected_in_group = selected & group_option_ids
        if (
            len(selected_in_group) < group.min_selections
            or len(selected_in_group) > group.max_selections
        ):
            raise modifier_invalid()
        for option in group.options:
            option_prices[option.option_id] = option.price_delta_minor
    if not selected <= set(option_prices):
        raise modifier_invalid()

    return variant.price_minor + sum(option_prices[option_id] for option_id in selected)


def hash_submit_request(*, command: SubmitOrderCommand, cart_items) -> str:
    payload = {
        "cartVersion": command.cart_version,
        "cartItemIds": sorted(command.cart_item_ids),
        "items": [
            {
                "clientCartItemId": row["client_cart_item_id"],
                "productId": str(row["product_service_id"]),
                "variantId": str(row["product_variant_id"]),
                "quantity": row["quantity"],
                "selectedModifiers": row["selected_modifiers"],
                "note": row["note"],
            }
            for row in cart_items
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


def session_expired() -> ApiError:
    return ApiError(status_code=401, code="session_expired", message="Session expired.")


def not_authorized() -> ApiError:
    return ApiError(status_code=403, code="not_authorized", message="Not authorized.")


def not_found_or_hidden() -> ApiError:
    return ApiError(status_code=404, code="not_found_or_hidden", message="Not found.")


def validation_failed(message: str) -> ApiError:
    return ApiError(status_code=422, code="validation_failed", message=message)


def item_not_orderable() -> ApiError:
    return ApiError(status_code=422, code="item_not_orderable", message="Item is not orderable.")


def variant_invalid() -> ApiError:
    return ApiError(status_code=422, code="variant_invalid", message="Variant is invalid.")


def modifier_invalid() -> ApiError:
    return ApiError(
        status_code=422,
        code="modifier_invalid",
        message="Modifier selection is invalid.",
    )


def fresh_presence_required() -> ApiError:
    return ApiError(
        status_code=403,
        code="fresh_presence_required",
        message="Fresh table presence is required.",
    )


def empty_cart() -> ApiError:
    return ApiError(status_code=422, code="empty_cart", message="Cart is empty.")


def idempotency_conflict() -> ApiError:
    return ApiError(
        status_code=409,
        code="idempotency_conflict",
        message="Idempotency key was used with a different request.",
    )


def closed_table_session() -> ApiError:
    return ApiError(
        status_code=409,
        code="closed_table_session",
        message="Table session cannot accept new orders.",
    )
