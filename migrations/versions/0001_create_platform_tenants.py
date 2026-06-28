"""create platform tenants

Revision ID: 0001_create_platform_tenants
Revises:
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_platform_tenants"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    tenant_status = sa.Enum("draft", "active", "suspended", name="tenant_status")
    tenant_status.create(op.get_bind())

    op.create_table(
        "platform_tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("status", tenant_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_platform_tenants_slug", "platform_tenants", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_platform_tenants_slug", table_name="platform_tenants")
    op.drop_table("platform_tenants")
    sa.Enum(name="tenant_status").drop(op.get_bind())
