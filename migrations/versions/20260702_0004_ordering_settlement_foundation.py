"""create ordering and settlement foundation

Revision ID: 20260702_0004
Revises: 20260702_0003
Create Date: 2026-07-02 17:31:53.261810+00:00

Rollback note:
- Safe to downgrade only before customer orders, table sessions, checks, payments,
  or cashier correction records exist. After use, dropping these tables requires
  explicit operational/audit data-retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0004"
down_revision: str | Sequence[str] | None = "20260702_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "table_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("table_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'open' and closed_at is null) "
            "or (status = 'closed' and closed_at is not null)",
            name=op.f("ck_table_sessions__closed_at_lifecycle"),
        ),
        sa.CheckConstraint("status in ('open', 'closed')", name=op.f("ck_table_sessions__status")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_table_sessions__tenant_venue_tables",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_table_sessions__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_table_sessions")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_table_sessions__tenant_id_id"),
    )
    op.create_index(
        "ix_table_sessions__tenant_status_opened",
        "table_sessions",
        ["tenant_id", "status", sa.literal_column("opened_at DESC")],
        unique=False,
    )
    op.create_index(
        "uq_table_sessions__tenant_table_open",
        "table_sessions",
        ["tenant_id", "table_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "checks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("table_session_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status = 'open' and closed_at is null) "
            "or (status = 'closed' and closed_at is not null)",
            name=op.f("ck_checks__closed_at_lifecycle"),
        ),
        sa.CheckConstraint("status in ('open', 'closed')", name=op.f("ck_checks__status")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_session_id"],
            ["table_sessions.tenant_id", "table_sessions.id"],
            name="fk_checks__tenant_table_sessions",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_checks__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checks")),
        sa.UniqueConstraint("table_session_id", name="uq_checks__table_session_id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_checks__tenant_id_id"),
    )
    op.create_table(
        "customer_ordering_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("table_id", sa.UUID(), nullable=False),
        sa.Column("table_session_id", sa.UUID(), nullable=True),
        sa.Column("cookie_token_hash", sa.Text(), nullable=False),
        sa.Column("presence_valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "presence_valid_until <= expires_at",
            name=op.f("ck_customer_ordering_sessions__presence_within_session"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_customer_ordering_sessions__tenant_venue_tables",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_session_id"],
            ["table_sessions.tenant_id", "table_sessions.id"],
            name="fk_customer_ordering_sessions__tenant_table_sessions",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_customer_ordering_sessions__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_ordering_sessions")),
        sa.UniqueConstraint(
            "cookie_token_hash", name="uq_customer_ordering_sessions__cookie_token_hash"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_customer_ordering_sessions__tenant_id_id"),
    )
    op.create_index(
        "ix_customer_ordering_sessions__tenant_table_last_seen",
        "customer_ordering_sessions",
        ["tenant_id", "table_id", sa.literal_column("last_seen_at DESC")],
        unique=False,
    )
    op.create_table(
        "cashier_corrections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("check_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("reason <> ''", name=op.f("ck_cashier_corrections__reason_required")),
        sa.CheckConstraint(
            "type in ('note', 'item_void', 'payment_void')",
            name=op.f("ck_cashier_corrections__type"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "check_id"],
            ["checks.tenant_id", "checks.id"],
            name="fk_cashier_corrections__tenant_checks",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_cashier_corrections__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_cashier_corrections__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cashier_corrections")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_cashier_corrections__tenant_id_id"),
    )
    op.create_index(
        "ix_cashier_corrections__tenant_check_created",
        "cashier_corrections",
        ["tenant_id", "check_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "customer_carts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_ordering_session_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('active', 'submitted', 'abandoned')", name=op.f("ck_customer_carts__status")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_ordering_session_id"],
            ["customer_ordering_sessions.tenant_id", "customer_ordering_sessions.id"],
            name="fk_customer_carts__tenant_customer_ordering_sessions",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_customer_carts__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_carts")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_customer_carts__tenant_id_id"),
    )
    op.create_index(
        "uq_customer_carts__tenant_customer_session_active",
        "customer_carts",
        ["tenant_id", "customer_ordering_session_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_ordering_session_id", sa.UUID(), nullable=False),
        sa.Column("table_session_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("order_channel", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "order_channel in ('dine_in_qr')", name=op.f("ck_orders__order_channel")
        ),
        sa.CheckConstraint("status in ('submitted')", name=op.f("ck_orders__status")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_ordering_session_id"],
            ["customer_ordering_sessions.tenant_id", "customer_ordering_sessions.id"],
            name="fk_orders__tenant_customer_ordering_sessions",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_session_id"],
            ["table_sessions.tenant_id", "table_sessions.id"],
            name="fk_orders__tenant_table_sessions",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_orders__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_orders__tenant_id_id"),
    )
    op.create_index(
        "ix_orders__tenant_customer_session_submitted",
        "orders",
        ["tenant_id", "customer_ordering_session_id", sa.literal_column("submitted_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_orders__tenant_table_session_submitted",
        "orders",
        ["tenant_id", "table_session_id", sa.literal_column("submitted_at DESC")],
        unique=False,
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("check_id", sa.UUID(), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.CHAR(length=3), server_default="TRY", nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("cashier_user_id", sa.UUID(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by_user_id", sa.UUID(), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'recorded' and voided_at is null "
            "and voided_by_user_id is null and void_reason is null) "
            "or (status = 'voided' and voided_at is not null "
            "and voided_by_user_id is not null and void_reason is not null "
            "and void_reason <> '')",
            name=op.f("ck_payments__void_lifecycle"),
        ),
        sa.CheckConstraint(
            "method in ('cash', 'card', 'transfer')", name=op.f("ck_payments__method")
        ),
        sa.CheckConstraint("status in ('recorded', 'voided')", name=op.f("ck_payments__status")),
        sa.CheckConstraint("amount_minor > 0", name=op.f("ck_payments__amount_positive")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cashier_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_payments__tenant_cashier_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "check_id"],
            ["checks.tenant_id", "checks.id"],
            name="fk_payments__tenant_checks",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "voided_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_payments__tenant_void_users",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_payments__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_payments__tenant_id_id"),
    )
    op.create_index(
        "ix_payments__tenant_check_received",
        "payments",
        ["tenant_id", "check_id", sa.literal_column("received_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_payments__tenant_received",
        "payments",
        ["tenant_id", sa.literal_column("received_at DESC")],
        unique=False,
    )
    op.create_table(
        "session_closures",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("table_session_id", sa.UUID(), nullable=False),
        sa.Column("check_id", sa.UUID(), nullable=False),
        sa.Column("cashier_user_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cashier_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_session_closures__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "check_id"],
            ["checks.tenant_id", "checks.id"],
            name="fk_session_closures__tenant_checks",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_session_id"],
            ["table_sessions.tenant_id", "table_sessions.id"],
            name="fk_session_closures__tenant_table_sessions",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_session_closures__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_closures")),
        sa.UniqueConstraint("table_session_id", name="uq_session_closures__table_session_id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_session_closures__tenant_id_id"),
    )
    op.create_table(
        "cashier_correction_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("check_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("cashier_correction_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status <> 'completed' "
            "or (cashier_correction_id is not null and completed_at is not null)",
            name=op.f("ck_cashier_correction_idempotency__completed_result"),
        ),
        sa.CheckConstraint(
            "status in ('processing', 'completed', 'failed')",
            name=op.f("ck_cashier_correction_idempotency__status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cashier_correction_id"],
            ["cashier_corrections.tenant_id", "cashier_corrections.id"],
            name="fk_cashier_correction_idempotency__tenant_cashier_corrections",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "check_id"],
            ["checks.tenant_id", "checks.id"],
            name="fk_cashier_correction_idempotency__tenant_checks",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_cashier_correction_idempotency__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cashier_correction_idempotency")),
        sa.UniqueConstraint(
            "tenant_id",
            "check_id",
            "idempotency_key",
            name="uq_cashier_correction_idempotency__tenant_check_key",
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_cashier_correction_idempotency__tenant_id_id"
        ),
    )
    op.create_table(
        "customer_cart_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("client_cart_item_id", sa.Text(), nullable=False),
        sa.Column("product_service_id", sa.UUID(), nullable=False),
        sa.Column("product_variant_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("selected_modifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("estimated_price_minor", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_customer_cart_items__quantity_positive")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "cart_id"],
            ["customer_carts.tenant_id", "customer_carts.id"],
            name="fk_customer_cart_items__tenant_customer_carts",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id", "product_variant_id"],
            [
                "product_variants.tenant_id",
                "product_variants.product_service_id",
                "product_variants.id",
            ],
            name="fk_customer_cart_items__tenant_product_variants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id"],
            ["product_services.tenant_id", "product_services.id"],
            name="fk_customer_cart_items__tenant_product_services",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_customer_cart_items__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_cart_items")),
        sa.UniqueConstraint(
            "tenant_id",
            "cart_id",
            "client_cart_item_id",
            name="uq_customer_cart_items__tenant_cart_client_item",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_customer_cart_items__tenant_id_id"),
    )
    op.create_index(
        "ix_customer_cart_items__tenant_cart",
        "customer_cart_items",
        ["tenant_id", "cart_id"],
        unique=False,
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_service_id", sa.UUID(), nullable=False),
        sa.Column("product_variant_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=False),
        sa.Column("name_snapshot", sa.Text(), nullable=False),
        sa.Column("variant_name_snapshot", sa.Text(), nullable=False),
        sa.Column("unit_price_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.CHAR(length=3), server_default="TRY", nullable=False),
        sa.Column("modifier_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_by_user_id", sa.UUID(), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(voided_at is null and voided_by_user_id is null and void_reason is null) "
            "or (voided_at is not null and voided_by_user_id is not null "
            "and void_reason is not null and void_reason <> '')",
            name=op.f("ck_order_items__void_fields_complete"),
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_order_items__quantity_positive")),
        sa.CheckConstraint(
            "unit_price_minor >= 0", name=op.f("ck_order_items__unit_price_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["orders.tenant_id", "orders.id"],
            name="fk_order_items__tenant_orders",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id", "product_variant_id"],
            [
                "product_variants.tenant_id",
                "product_variants.product_service_id",
                "product_variants.id",
            ],
            name="fk_order_items__tenant_product_variants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id"],
            ["product_services.tenant_id", "product_services.id"],
            name="fk_order_items__tenant_product_services",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "station_id"],
            ["stations.tenant_id", "stations.id"],
            name="fk_order_items__tenant_stations",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "voided_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_order_items__tenant_void_users",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_order_items__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_items")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_order_items__tenant_id_id"),
    )
    op.create_index(
        "ix_order_items__tenant_order", "order_items", ["tenant_id", "order_id"], unique=False
    )
    op.create_table(
        "order_submit_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("customer_ordering_session_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status <> 'completed' or (order_id is not null and completed_at is not null)",
            name=op.f("ck_order_submit_idempotency__completed_result"),
        ),
        sa.CheckConstraint(
            "status in ('processing', 'completed', 'failed')",
            name=op.f("ck_order_submit_idempotency__status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_ordering_session_id"],
            ["customer_ordering_sessions.tenant_id", "customer_ordering_sessions.id"],
            name="fk_order_submit_idempotency__tenant_customer_ordering_sessions",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["orders.tenant_id", "orders.id"],
            name="fk_order_submit_idempotency__tenant_orders",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_order_submit_idempotency__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_submit_idempotency")),
        sa.UniqueConstraint(
            "tenant_id",
            "customer_ordering_session_id",
            "idempotency_key",
            name="uq_order_submit_idempotency__tenant_session_key",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_order_submit_idempotency__tenant_id_id"),
    )
    op.create_table(
        "payment_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("check_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status <> 'completed' or (payment_id is not null and completed_at is not null)",
            name=op.f("ck_payment_idempotency__completed_result"),
        ),
        sa.CheckConstraint(
            "status in ('processing', 'completed', 'failed')",
            name=op.f("ck_payment_idempotency__status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "check_id"],
            ["checks.tenant_id", "checks.id"],
            name="fk_payment_idempotency__tenant_checks",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            name="fk_payment_idempotency__tenant_payments",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_payment_idempotency__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_idempotency")),
        sa.UniqueConstraint(
            "tenant_id",
            "check_id",
            "idempotency_key",
            name="uq_payment_idempotency__tenant_check_key",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_payment_idempotency__tenant_id_id"),
    )
    op.create_table(
        "payment_void_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status <> 'completed' or completed_at is not null",
            name=op.f("ck_payment_void_idempotency__completed_result"),
        ),
        sa.CheckConstraint(
            "status in ('processing', 'completed', 'failed')",
            name=op.f("ck_payment_void_idempotency__status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
            name="fk_payment_void_idempotency__tenant_payments",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_payment_void_idempotency__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_void_idempotency")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_payment_void_idempotency__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "payment_id",
            "idempotency_key",
            name="uq_payment_void_idempotency__tenant_payment_key",
        ),
    )
    op.create_table(
        "price_adjustments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("check_id", sa.UUID(), nullable=False),
        sa.Column("order_item_id", sa.UUID(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.CHAR(length=3), server_default="TRY", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type <> 'correction' or (reason is not null and reason <> '')",
            name=op.f("ck_price_adjustments__correction_reason"),
        ),
        sa.CheckConstraint(
            "type in ('tax', 'discount', 'service_charge', 'campaign', 'correction')",
            name=op.f("ck_price_adjustments__type"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "check_id"],
            ["checks.tenant_id", "checks.id"],
            name="fk_price_adjustments__tenant_checks",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_price_adjustments__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_item_id"],
            ["order_items.tenant_id", "order_items.id"],
            name="fk_price_adjustments__tenant_order_items",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_price_adjustments__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_price_adjustments")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_price_adjustments__tenant_id_id"),
    )


def downgrade() -> None:
    op.drop_table("price_adjustments")
    op.drop_table("payment_void_idempotency")
    op.drop_table("payment_idempotency")
    op.drop_table("order_submit_idempotency")
    op.drop_index("ix_order_items__tenant_order", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_customer_cart_items__tenant_cart", table_name="customer_cart_items")
    op.drop_table("customer_cart_items")
    op.drop_table("cashier_correction_idempotency")
    op.drop_table("session_closures")
    op.drop_index("ix_payments__tenant_received", table_name="payments")
    op.drop_index("ix_payments__tenant_check_received", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_orders__tenant_table_session_submitted", table_name="orders")
    op.drop_index("ix_orders__tenant_customer_session_submitted", table_name="orders")
    op.drop_table("orders")
    op.drop_index(
        "uq_customer_carts__tenant_customer_session_active",
        table_name="customer_carts",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_table("customer_carts")
    op.drop_index("ix_cashier_corrections__tenant_check_created", table_name="cashier_corrections")
    op.drop_table("cashier_corrections")
    op.drop_index(
        "ix_customer_ordering_sessions__tenant_table_last_seen",
        table_name="customer_ordering_sessions",
    )
    op.drop_table("customer_ordering_sessions")
    op.drop_table("checks")
    op.drop_index(
        "uq_table_sessions__tenant_table_open",
        table_name="table_sessions",
        postgresql_where=sa.text("status = 'open'"),
    )
    op.drop_index("ix_table_sessions__tenant_status_opened", table_name="table_sessions")
    op.drop_table("table_sessions")
