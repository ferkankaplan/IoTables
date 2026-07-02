"""create table display and presence foundation

Revision ID: 20260702_0003
Revises: 20260702_0002
Create Date: 2026-07-02 00:00:00 UTC

Rollback note:
- Safe to downgrade only before table display credentials, provisioning claims, or QR
  token history exist. After use, dropping these tables requires explicit
  security/audit retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0003"
down_revision: str | Sequence[str] | None = "20260702_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "table_display_claims",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("table_id", UUID, nullable=False),
        sa.Column("claim_hash", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", UUID, nullable=False),
        sa.Column("expires_at", TIMESTAMPTZ, nullable=False),
        sa.Column("consumed_at", TIMESTAMPTZ),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_table_display_claims"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_table_display_claims__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_table_display_claims__tenant_venue_tables",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_table_display_claims__tenant_users",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_table_display_claims__tenant_id_id"),
        sa.UniqueConstraint("claim_hash", name="uq_table_display_claims__claim_hash"),
        sa.CheckConstraint(
            "consumed_at is null or consumed_at <= expires_at",
            name=op.f("ck_table_display_claims__consumed_before_expiry"),
        ),
    )
    op.create_index(
        "ix_table_display_claims__tenant_table_created",
        "table_display_claims",
        ["tenant_id", "table_id", sa.text("created_at desc")],
    )

    op.create_table(
        "table_display_credentials",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("table_id", UUID, nullable=False),
        sa.Column("credential_hash", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("provisioned_at", TIMESTAMPTZ, nullable=False),
        sa.Column("revoked_at", TIMESTAMPTZ),
        sa.Column("last_seen_at", TIMESTAMPTZ),
        sa.PrimaryKeyConstraint("id", name="pk_table_display_credentials"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_table_display_credentials__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_table_display_credentials__tenant_venue_tables",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_table_display_credentials__tenant_id_id"),
        sa.UniqueConstraint(
            "credential_hash",
            name="uq_table_display_credentials__credential_hash",
        ),
        sa.CheckConstraint(
            "status in ('active', 'revoked')",
            name=op.f("ck_table_display_credentials__status"),
        ),
        sa.CheckConstraint(
            "(status = 'active' and revoked_at is null) "
            "or (status = 'revoked' and revoked_at is not null)",
            name=op.f("ck_table_display_credentials__revocation_lifecycle"),
        ),
    )
    op.create_index(
        "uq_table_display_credentials__tenant_table_active",
        "table_display_credentials",
        ["tenant_id", "table_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_table_display_credentials__tenant_table",
        "table_display_credentials",
        ["tenant_id", "table_id"],
    )

    op.create_table(
        "table_access_tokens",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("table_id", UUID, nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", TIMESTAMPTZ, nullable=False),
        sa.Column("consumed_at", TIMESTAMPTZ),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_table_access_tokens"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_table_access_tokens__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_table_access_tokens__tenant_venue_tables",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_table_access_tokens__tenant_id_id"),
        sa.UniqueConstraint("token_hash", name="uq_table_access_tokens__token_hash"),
        sa.CheckConstraint(
            "consumed_at is null or consumed_at <= expires_at",
            name=op.f("ck_table_access_tokens__consumed_before_expiry"),
        ),
    )
    op.create_index(
        "ix_table_access_tokens__tenant_table_created",
        "table_access_tokens",
        ["tenant_id", "table_id", sa.text("created_at desc")],
    )


def downgrade() -> None:
    op.drop_table("table_access_tokens")
    op.drop_table("table_display_credentials")
    op.drop_table("table_display_claims")
