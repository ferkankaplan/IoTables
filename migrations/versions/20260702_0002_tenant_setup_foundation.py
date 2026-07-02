"""create tenant setup foundation

Revision ID: 20260702_0002
Revises: 20260701_0001
Create Date: 2026-07-02 00:00:00 UTC

Rollback note:
- Safe to downgrade only before tenant setup/menu/staff assignment data exists. After use,
  dropping these tables requires explicit data-retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0002"
down_revision: str | Sequence[str] | None = "20260701_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "halls",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_halls"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_halls__tenants"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_halls__tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "display_order", name="uq_halls__tenant_display_order"),
    )
    op.create_index(
        "uq_halls__tenant_name_lower",
        "halls",
        ["tenant_id", sa.text("lower(name)")],
        unique=True,
    )

    op.create_table(
        "venue_tables",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("hall_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_venue_tables"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_venue_tables__tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "hall_id"],
            ["halls.tenant_id", "halls.id"],
            name="fk_venue_tables__tenant_halls",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_venue_tables__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "hall_id",
            "display_order",
            name="uq_venue_tables__tenant_hall_display_order",
        ),
    )
    op.create_index(
        "uq_venue_tables__tenant_hall_name_lower",
        "venue_tables",
        ["tenant_id", "hall_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index(
        "ix_venue_tables__tenant_hall_display",
        "venue_tables",
        ["tenant_id", "hall_id", "display_order"],
    )

    op.create_table(
        "stations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_stations"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_stations__tenants"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_stations__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "display_order",
            name="uq_stations__tenant_display_order",
        ),
    )
    op.create_index(
        "uq_stations__tenant_name_lower",
        "stations",
        ["tenant_id", sa.text("lower(name)")],
        unique=True,
    )

    op.create_table(
        "menu_categories",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_menu_categories"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_menu_categories__tenants"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_menu_categories__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "display_order",
            name="uq_menu_categories__tenant_display_order",
        ),
    )
    op.create_index(
        "uq_menu_categories__tenant_name_lower",
        "menu_categories",
        ["tenant_id", sa.text("lower(name)")],
        unique=True,
    )

    op.create_table(
        "product_services",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("category_id", UUID, nullable=False),
        sa.Column("station_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("image_ref", sa.Text()),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_product_services"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_product_services__tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "category_id"],
            ["menu_categories.tenant_id", "menu_categories.id"],
            name="fk_product_services__tenant_menu_categories",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "station_id"],
            ["stations.tenant_id", "stations.id"],
            name="fk_product_services__tenant_stations",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_product_services__tenant_id_id"),
    )
    op.create_index(
        "uq_product_services__tenant_category_name_lower",
        "product_services",
        ["tenant_id", "category_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index(
        "ix_product_services__tenant_category_enabled_name",
        "product_services",
        ["tenant_id", "category_id", "enabled", "name"],
    )
    op.create_index(
        "ix_product_services__tenant_enabled_category",
        "product_services",
        ["tenant_id", "enabled", "category_id"],
    )
    op.create_index(
        "ix_product_services__tenant_station",
        "product_services",
        ["tenant_id", "station_id"],
    )

    op.create_table(
        "product_variants",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("product_service_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.CHAR(3), server_default="TRY", nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_product_variants"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_product_variants__tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id"],
            ["product_services.tenant_id", "product_services.id"],
            name="fk_product_variants__tenant_product_services",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_product_variants__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "product_service_id",
            "id",
            name="uq_product_variants__tenant_product_id",
        ),
        sa.CheckConstraint(
            "price_minor >= 0",
            name=op.f("ck_product_variants__price_minor_non_negative"),
        ),
    )
    op.create_index(
        "uq_product_variants__tenant_product_name_lower",
        "product_variants",
        ["tenant_id", "product_service_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index(
        "uq_product_variants__tenant_product_default",
        "product_variants",
        ["tenant_id", "product_service_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )
    op.create_index(
        "ix_product_variants__tenant_product_display",
        "product_variants",
        ["tenant_id", "product_service_id", "display_order"],
    )
    op.create_index(
        "ix_product_variants__tenant_product_enabled",
        "product_variants",
        ["tenant_id", "product_service_id", "enabled"],
    )

    op.create_table(
        "availability_overrides",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("product_service_id", UUID, nullable=False),
        sa.Column("product_variant_id", UUID),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("starts_at", TIMESTAMPTZ),
        sa.Column("expires_at", TIMESTAMPTZ),
        sa.Column("created_by_user_id", UUID, nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_availability_overrides"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_availability_overrides__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id"],
            ["product_services.tenant_id", "product_services.id"],
            name="fk_availability_overrides__tenant_product_services",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id", "product_variant_id"],
            [
                "product_variants.tenant_id",
                "product_variants.product_service_id",
                "product_variants.id",
            ],
            name="fk_availability_overrides__tenant_product_variants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_availability_overrides__tenant_users",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_availability_overrides__tenant_id_id"),
        sa.CheckConstraint(
            "state in ('available', 'unavailable')",
            name=op.f("ck_availability_overrides__state"),
        ),
        sa.CheckConstraint(
            "expires_at is null or starts_at is null or expires_at > starts_at",
            name=op.f("ck_availability_overrides__valid_time_window"),
        ),
    )
    op.create_index(
        "ix_availability_overrides__tenant_product",
        "availability_overrides",
        ["tenant_id", "product_service_id", "product_variant_id"],
    )

    op.create_table(
        "modifier_groups",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("product_service_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("min_selections", sa.Integer(), nullable=False),
        sa.Column("max_selections", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_modifier_groups"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_modifier_groups__tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "product_service_id"],
            ["product_services.tenant_id", "product_services.id"],
            name="fk_modifier_groups__tenant_product_services",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_modifier_groups__tenant_id_id"),
        sa.CheckConstraint(
            "min_selections >= 0 and max_selections >= min_selections",
            name=op.f("ck_modifier_groups__selection_bounds"),
        ),
    )
    op.create_index(
        "uq_modifier_groups__tenant_product_name_lower",
        "modifier_groups",
        ["tenant_id", "product_service_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index(
        "ix_modifier_groups__tenant_product_display",
        "modifier_groups",
        ["tenant_id", "product_service_id", "display_order"],
    )

    op.create_table(
        "modifier_options",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("modifier_group_id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("price_delta_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.CHAR(3), server_default="TRY", nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_modifier_options"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_modifier_options__tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "modifier_group_id"],
            ["modifier_groups.tenant_id", "modifier_groups.id"],
            name="fk_modifier_options__tenant_modifier_groups",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_modifier_options__tenant_id_id"),
        sa.CheckConstraint(
            "price_delta_minor >= 0",
            name=op.f("ck_modifier_options__price_delta_non_negative"),
        ),
    )
    op.create_index(
        "uq_modifier_options__tenant_group_name_lower",
        "modifier_options",
        ["tenant_id", "modifier_group_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index(
        "ix_modifier_options__tenant_group_display",
        "modifier_options",
        ["tenant_id", "modifier_group_id", "display_order"],
    )

    op.create_table(
        "staff_station_assignments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("station_id", UUID, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("revoked_at", TIMESTAMPTZ),
        sa.PrimaryKeyConstraint("id", name="pk_staff_station_assignments"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_staff_station_assignments__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_staff_station_assignments__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "station_id"],
            ["stations.tenant_id", "stations.id"],
            name="fk_staff_station_assignments__tenant_stations",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_staff_station_assignments__tenant_id_id"),
        sa.CheckConstraint(
            "status in ('active', 'revoked')",
            name=op.f("ck_staff_station_assignments__status"),
        ),
    )
    op.create_index(
        "uq_staff_station_assignments__tenant_user_station_active",
        "staff_station_assignments",
        ["tenant_id", "user_id", "station_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_staff_station_assignments__tenant_user_active",
        "staff_station_assignments",
        ["tenant_id", "user_id"],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_staff_station_assignments__tenant_station",
        "staff_station_assignments",
        ["tenant_id", "station_id"],
    )

    op.create_table(
        "staff_hall_assignments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("hall_id", UUID, nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("revoked_at", TIMESTAMPTZ),
        sa.PrimaryKeyConstraint("id", name="pk_staff_hall_assignments"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_staff_hall_assignments__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_staff_hall_assignments__tenant_users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "hall_id"],
            ["halls.tenant_id", "halls.id"],
            name="fk_staff_hall_assignments__tenant_halls",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_staff_hall_assignments__tenant_id_id"),
        sa.CheckConstraint(
            "status in ('active', 'revoked')",
            name=op.f("ck_staff_hall_assignments__status"),
        ),
    )
    op.create_index(
        "uq_staff_hall_assignments__tenant_user_hall_active",
        "staff_hall_assignments",
        ["tenant_id", "user_id", "hall_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_staff_hall_assignments__tenant_user_active",
        "staff_hall_assignments",
        ["tenant_id", "user_id"],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_staff_hall_assignments__tenant_hall",
        "staff_hall_assignments",
        ["tenant_id", "hall_id"],
    )


def downgrade() -> None:
    op.drop_table("staff_hall_assignments")
    op.drop_table("staff_station_assignments")
    op.drop_table("modifier_options")
    op.drop_table("modifier_groups")
    op.drop_table("availability_overrides")
    op.drop_table("product_variants")
    op.drop_table("product_services")
    op.drop_table("menu_categories")
    op.drop_table("stations")
    op.drop_table("venue_tables")
    op.drop_table("halls")
