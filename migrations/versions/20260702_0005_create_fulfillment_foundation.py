"""create fulfillment foundation

Revision ID: 20260702_0005
Revises: 20260702_0004
Create Date: 2026-07-02 17:58:03.946813+00:00

Rollback note:
- Safe to downgrade only before preparation, delivery, or service bulk
  idempotency records exist. After use, dropping these tables requires explicit
  operational/audit data-retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0005"
down_revision: str | Sequence[str] | None = "20260702_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_order_items__tenant_id_id_station_id",
        "order_items",
        ["tenant_id", "id", "station_id"],
    )
    op.create_table(
        "delivery_bulk_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("table_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column(
            "delivered_order_item_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "delivered_order_item_ids is null or jsonb_typeof(delivered_order_item_ids) = 'array'",
            name=op.f("ck_delivery_bulk_idempotency__delivered_order_item_ids_array"),
        ),
        sa.CheckConstraint(
            "status <> 'completed' or "
            "(completed_at is not null and delivered_order_item_ids is not null)",
            name=op.f("ck_delivery_bulk_idempotency__completed_result"),
        ),
        sa.CheckConstraint(
            "status in ('processing', 'completed', 'failed')",
            name=op.f("ck_delivery_bulk_idempotency__status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_delivery_bulk_idempotency__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_delivery_bulk_idempotency__tenant_venue_tables",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_delivery_bulk_idempotency__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_bulk_idempotency")),
        sa.UniqueConstraint(
            "tenant_id",
            "actor_user_id",
            "idempotency_key",
            name="uq_delivery_bulk_idempotency__tenant_actor_key",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_delivery_bulk_idempotency__tenant_id_id"),
    )
    op.create_table(
        "delivery_states",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_item_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("updated_by_user_id", sa.UUID(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('picked_up', 'delivered')", name=op.f("ck_delivery_states__status")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_item_id"],
            ["order_items.tenant_id", "order_items.id"],
            name="fk_delivery_states__tenant_order_items",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "updated_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_delivery_states__tenant_updated_users",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_delivery_states__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_states")),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            "order_item_id",
            name="uq_delivery_states__tenant_id_id_order_item_id",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_delivery_states__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id", "order_item_id", name="uq_delivery_states__tenant_order_item"
        ),
    )
    op.create_index(
        "ix_delivery_states__tenant_status_updated",
        "delivery_states",
        ["tenant_id", "status", sa.literal_column("updated_at DESC")],
        unique=False,
    )
    op.create_table(
        "preparation_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("order_item_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("cannot_prepare_reason", sa.Text(), nullable=True),
        sa.Column("updated_by_user_id", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status = 'cannot_prepare' and cannot_prepare_reason is not null "
            "and cannot_prepare_reason <> '') or "
            "(status <> 'cannot_prepare' and cannot_prepare_reason is null)",
            name=op.f("ck_preparation_items__cannot_prepare_reason_lifecycle"),
        ),
        sa.CheckConstraint(
            "status = 'pending' or updated_by_user_id is not null",
            name=op.f("ck_preparation_items__non_pending_actor_required"),
        ),
        sa.CheckConstraint(
            "status in ('pending', 'preparing', 'ready', 'cannot_prepare')",
            name=op.f("ck_preparation_items__status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "order_item_id", "station_id"],
            ["order_items.tenant_id", "order_items.id", "order_items.station_id"],
            name="fk_preparation_items__tenant_order_items_station",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "station_id"],
            ["stations.tenant_id", "stations.id"],
            name="fk_preparation_items__tenant_stations",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "updated_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_preparation_items__tenant_updated_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_preparation_items__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_preparation_items")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_preparation_items__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id", "order_item_id", name="uq_preparation_items__tenant_order_item"
        ),
    )
    op.create_index(
        "ix_preparation_items__tenant_station_status_updated",
        "preparation_items",
        ["tenant_id", "station_id", "status", sa.literal_column("updated_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_preparation_items__tenant_status_updated",
        "preparation_items",
        ["tenant_id", "status", sa.literal_column("updated_at DESC")],
        unique=False,
    )
    op.create_table(
        "delivery_transitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("delivery_state_id", sa.UUID(), nullable=False),
        sa.Column("order_item_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(from_status is null and to_status in ('picked_up', 'delivered')) or "
            "(from_status = 'picked_up' and to_status = 'delivered')",
            name=op.f("ck_delivery_transitions__valid_transition"),
        ),
        sa.CheckConstraint(
            "from_status is null or from_status = 'picked_up'",
            name=op.f("ck_delivery_transitions__from_status"),
        ),
        sa.CheckConstraint(
            "to_status in ('picked_up', 'delivered')",
            name=op.f("ck_delivery_transitions__to_status"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_delivery_transitions__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "delivery_state_id", "order_item_id"],
            ["delivery_states.tenant_id", "delivery_states.id", "delivery_states.order_item_id"],
            name="fk_delivery_transitions__tenant_delivery_states",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_delivery_transitions__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_transitions")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_delivery_transitions__tenant_id_id"),
    )
    op.create_index(
        "ix_delivery_transitions__tenant_item_created",
        "delivery_transitions",
        ["tenant_id", "order_item_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "preparation_transitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("preparation_item_id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(from_status is null and to_status = 'pending') or "
            "(from_status = 'pending' and to_status in ('preparing', 'cannot_prepare')) or "
            "(from_status = 'preparing' and to_status in ('ready', 'cannot_prepare'))",
            name=op.f("ck_preparation_transitions__valid_transition"),
        ),
        sa.CheckConstraint(
            "(to_status = 'cannot_prepare' and reason is not null and reason <> '') or "
            "(to_status <> 'cannot_prepare' and reason is null)",
            name=op.f("ck_preparation_transitions__cannot_prepare_reason_lifecycle"),
        ),
        sa.CheckConstraint(
            "from_status is null or from_status in "
            "('pending', 'preparing', 'ready', 'cannot_prepare')",
            name=op.f("ck_preparation_transitions__from_status"),
        ),
        sa.CheckConstraint(
            "to_status in ('pending', 'preparing', 'ready', 'cannot_prepare')",
            name=op.f("ck_preparation_transitions__to_status"),
        ),
        sa.CheckConstraint(
            "from_status is null or actor_user_id is not null",
            name=op.f("ck_preparation_transitions__actor_required_after_initial"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_preparation_transitions__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "preparation_item_id"],
            ["preparation_items.tenant_id", "preparation_items.id"],
            name="fk_preparation_transitions__tenant_preparation_items",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_preparation_transitions__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_preparation_transitions")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_preparation_transitions__tenant_id_id"),
    )
    op.create_index(
        "ix_preparation_transitions__tenant_item_created",
        "preparation_transitions",
        ["tenant_id", "preparation_item_id", sa.literal_column("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_preparation_transitions__tenant_item_created", table_name="preparation_transitions"
    )
    op.drop_table("preparation_transitions")
    op.drop_index("ix_delivery_transitions__tenant_item_created", table_name="delivery_transitions")
    op.drop_table("delivery_transitions")
    op.drop_index("ix_preparation_items__tenant_status_updated", table_name="preparation_items")
    op.drop_index(
        "ix_preparation_items__tenant_station_status_updated", table_name="preparation_items"
    )
    op.drop_table("preparation_items")
    op.drop_index("ix_delivery_states__tenant_status_updated", table_name="delivery_states")
    op.drop_table("delivery_states")
    op.drop_table("delivery_bulk_idempotency")
    op.drop_constraint(
        "uq_order_items__tenant_id_id_station_id",
        "order_items",
        type_="unique",
    )
