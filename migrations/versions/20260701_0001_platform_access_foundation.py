"""create platform and access foundation

Revision ID: 20260701_0001
Revises:
Create Date: 2026-07-01 00:00:00 UTC

Rollback note:
- Safe to downgrade only before production data exists. After tenant/user data exists,
  dropping these tables requires explicit data-retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260701_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", UUID, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("subdomain", sa.Text(), nullable=False),
        sa.Column("gsm_number", sa.Text(), nullable=False),
        sa.Column("sector", sa.Text()),
        sa.Column("capacity", sa.Integer()),
        sa.Column("address", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("dns_ready", sa.Boolean(), nullable=False),
        sa.Column("provisioning_error", sa.Text()),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenants"),
        sa.CheckConstraint(
            "sector is null or sector in ('cafe')",
            name=op.f("ck_tenants__sector"),
        ),
        sa.CheckConstraint(
            "status in ('provisioning', 'active', 'suspended', 'provisioning_failed')",
            name=op.f("ck_tenants__status"),
        ),
        sa.CheckConstraint(
            "capacity is null or capacity > 0",
            name=op.f("ck_tenants__capacity_positive"),
        ),
        sa.CheckConstraint(
            "provisioning_error is null or status = 'provisioning_failed'",
            name=op.f("ck_tenants__provisioning_error_status"),
        ),
    )
    op.create_index(
        "uq_tenants__subdomain_lower",
        "tenants",
        [sa.text("lower(subdomain)")],
        unique=True,
    )
    op.create_index(
        "ix_tenants__status_created",
        "tenants",
        ["status", sa.text("created_at desc")],
    )

    op.create_table(
        "tenant_operational_settings",
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("public_display_name", sa.Text()),
        sa.Column("service_delivery_tracking_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", name="pk_tenant_operational_settings"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_tenant_operational_settings__tenants",
        ),
    )

    op.create_table(
        "tenant_health",
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("lifecycle_state", sa.Text(), nullable=False),
        sa.Column("setup_state", sa.Text(), nullable=False),
        sa.Column("starter_template_state", sa.Text(), nullable=False),
        sa.Column("tenant_admin_bootstrap_state", sa.Text(), nullable=False),
        sa.Column("dns_ready", sa.Boolean(), nullable=False),
        sa.Column("runtime_error_summary", sa.Text()),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", name="pk_tenant_health"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_tenant_health__tenants",
        ),
    )
    op.create_index(
        "ix_tenant_health__updated",
        "tenant_health",
        [sa.text("updated_at desc")],
    )

    op.create_table(
        "starter_template_applications",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("sector", sa.Text(), nullable=False),
        sa.Column("template_key", sa.Text(), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("failure_summary", sa.Text()),
        sa.Column("applied_at", TIMESTAMPTZ),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_starter_template_applications"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_starter_template_applications__tenants",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_starter_template_applications__tenant_id_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "template_key",
            "template_version",
            name="uq_starter_template_applications__tenant_template_version",
        ),
        sa.CheckConstraint(
            "sector in ('cafe')",
            name=op.f("ck_starter_template_applications__sector"),
        ),
        sa.CheckConstraint(
            "status in ('pending', 'applied', 'failed', 'recovery_needed')",
            name=op.f("ck_starter_template_applications__status"),
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("first_password_change_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_users__tenants"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_users__tenant_id_id"),
        sa.CheckConstraint("status in ('active', 'disabled')", name=op.f("ck_users__status")),
    )
    op.create_index(
        "uq_users__tenant_username_lower",
        "users",
        ["tenant_id", sa.text("lower(username)")],
        unique=True,
        postgresql_where=sa.text("tenant_id is not null"),
    )
    op.create_index(
        "uq_users__platform_username_lower",
        "users",
        [sa.text("lower(username)")],
        unique=True,
        postgresql_where=sa.text("tenant_id is null"),
    )

    op.create_table(
        "credentials",
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("bootstrap_credential", sa.Boolean(), nullable=False),
        sa.Column("changed_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_credentials"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_credentials__users"),
    )

    op.create_table(
        "login_sessions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("app_scope", sa.Text(), nullable=False),
        sa.Column("session_token_hash", sa.Text(), nullable=False),
        sa.Column("issued_at", TIMESTAMPTZ, nullable=False),
        sa.Column("expires_at", TIMESTAMPTZ, nullable=False),
        sa.Column("revoked_at", TIMESTAMPTZ),
        sa.PrimaryKeyConstraint("id", name="pk_login_sessions"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_login_sessions__tenants",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_login_sessions__users"),
        sa.UniqueConstraint("session_token_hash", name="uq_login_sessions__session_token_hash"),
        sa.CheckConstraint(
            "app_scope in ('platform', 'tenant', 'cashier', 'station', 'service')",
            name=op.f("ck_login_sessions__app_scope"),
        ),
    )

    op.create_table(
        "platform_role_assignments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_platform_role_assignments"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_platform_role_assignments__users",
        ),
        sa.CheckConstraint(
            "role in ('platform_owner')",
            name=op.f("ck_platform_role_assignments__role"),
        ),
        sa.CheckConstraint(
            "status in ('active', 'disabled')",
            name=op.f("ck_platform_role_assignments__status"),
        ),
    )
    op.create_index(
        "uq_platform_role_assignments__active_platform_owner",
        "platform_role_assignments",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'platform_owner' and status = 'active'"),
    )

    op.create_table(
        "totp_factors",
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("secret_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("enrolled_at", TIMESTAMPTZ, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_totp_factors"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_totp_factors__users"),
    )

    op.create_table(
        "staff_profiles",
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_staff_profiles"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_staff_profiles__tenants"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_staff_profiles__tenant_users",
        ),
        sa.CheckConstraint(
            "status in ('active', 'disabled')",
            name=op.f("ck_staff_profiles__status"),
        ),
    )

    op.create_table(
        "staff_role_assignments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.Column("revoked_at", TIMESTAMPTZ),
        sa.PrimaryKeyConstraint("id", name="pk_staff_role_assignments"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_staff_role_assignments__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_staff_role_assignments__tenant_users",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_staff_role_assignments__tenant_id_id"),
        sa.CheckConstraint(
            "role in ('tenant_admin', 'cashier', 'station_staff', 'service_staff')",
            name=op.f("ck_staff_role_assignments__role"),
        ),
        sa.CheckConstraint(
            "status in ('active', 'revoked')",
            name=op.f("ck_staff_role_assignments__status"),
        ),
    )
    op.create_index(
        "uq_staff_role_assignments__tenant_user_role_active",
        "staff_role_assignments",
        ["tenant_id", "user_id", "role"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_staff_role_assignments__tenant_user_active",
        "staff_role_assignments",
        ["tenant_id", "user_id"],
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "tenant_lifecycle_events",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("previous_status", sa.Text()),
        sa.Column("next_status", sa.Text(), nullable=False),
        sa.Column("actor_user_id", UUID),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_lifecycle_events"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_tenant_lifecycle_events__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_tenant_lifecycle_events__users",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_tenant_lifecycle_events__tenant_id_id"),
        sa.CheckConstraint(
            "previous_status is null or previous_status in "
            "('provisioning', 'active', 'suspended', 'provisioning_failed')",
            name=op.f("ck_tenant_lifecycle_events__previous_status"),
        ),
        sa.CheckConstraint(
            "next_status in ('provisioning', 'active', 'suspended', 'provisioning_failed')",
            name=op.f("ck_tenant_lifecycle_events__next_status"),
        ),
        sa.CheckConstraint(
            "previous_status is null or previous_status is distinct from next_status",
            name=op.f("ck_tenant_lifecycle_events__status_transition"),
        ),
    )
    op.create_index(
        "ix_tenant_lifecycle_events__tenant_created",
        "tenant_lifecycle_events",
        ["tenant_id", sa.text("created_at desc")],
    )


def downgrade() -> None:
    op.drop_table("tenant_lifecycle_events")
    op.drop_table("staff_role_assignments")
    op.drop_table("staff_profiles")
    op.drop_table("totp_factors")
    op.drop_table("platform_role_assignments")
    op.drop_table("login_sessions")
    op.drop_table("credentials")
    op.drop_table("users")
    op.drop_table("starter_template_applications")
    op.drop_table("tenant_health")
    op.drop_table("tenant_operational_settings")
    op.drop_table("tenants")
