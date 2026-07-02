"""add tenant provisioning idempotency

Revision ID: 20260702_0008
Revises: 20260702_0007
Create Date: 2026-07-02 19:24:09.040690+00:00

Rollback note:
- Safe to downgrade only before tenant creation idempotency records exist. After
  use, dropping this table requires explicit provisioning history retention
  approval because replay evidence would be lost.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0008"
down_revision: str | Sequence[str] | None = "20260702_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_provisioning_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "idempotency_key <> ''",
            name=op.f("ck_tenant_provisioning_idempotency__idempotency_key_required"),
        ),
        sa.CheckConstraint(
            "request_hash <> ''",
            name=op.f("ck_tenant_provisioning_idempotency__request_hash_required"),
        ),
        sa.CheckConstraint(
            "response_payload is null or jsonb_typeof(response_payload) = 'object'",
            name=op.f("ck_tenant_provisioning_idempotency__response_payload_object"),
        ),
        sa.CheckConstraint(
            "status <> 'completed' or "
            "(tenant_id is not null and completed_at is not null and response_payload is not null)",
            name=op.f("ck_tenant_provisioning_idempotency__completed_result"),
        ),
        sa.CheckConstraint(
            "status in ('processing', 'completed', 'failed')",
            name=op.f("ck_tenant_provisioning_idempotency__status"),
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_tenant_provisioning_idempotency__users",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_tenant_provisioning_idempotency__tenants",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tenant_provisioning_idempotency")),
        sa.UniqueConstraint(
            "actor_user_id",
            "idempotency_key",
            name="uq_tenant_provisioning_idempotency__actor_key",
        ),
    )
    op.create_index(
        "ix_tenant_provisioning_idempotency__tenant",
        "tenant_provisioning_idempotency",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tenant_provisioning_idempotency__tenant",
        table_name="tenant_provisioning_idempotency",
    )
    op.drop_table("tenant_provisioning_idempotency")
