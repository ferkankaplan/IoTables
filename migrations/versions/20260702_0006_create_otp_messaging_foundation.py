"""create otp messaging foundation

Revision ID: 20260702_0006
Revises: 20260702_0005
Create Date: 2026-07-02 18:09:27.326138+00:00

Rollback note:
- Safe to downgrade only before OTP challenges, verification attempts, or SMS
  delivery records exist. After use, dropping these tables requires explicit
  security/audit data-retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260702_0006"
down_revision: str | Sequence[str] | None = "20260702_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("target_gsm", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("code_hash <> ''", name=op.f("ck_otp_challenges__code_hash_required")),
        sa.CheckConstraint(
            "purpose in ('tenant_admin_first_password', 'cashier_first_password')",
            name=op.f("ck_otp_challenges__purpose"),
        ),
        sa.CheckConstraint("target_gsm <> ''", name=op.f("ck_otp_challenges__target_gsm_required")),
        sa.CheckConstraint(
            "verified_at is null or verified_at <= expires_at",
            name=op.f("ck_otp_challenges__verified_before_expiry"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_otp_challenges__tenant_users",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_otp_challenges__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_otp_challenges")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_otp_challenges__tenant_id_id"),
    )
    op.create_index(
        "ix_otp_challenges__tenant_user_purpose_created",
        "otp_challenges",
        ["tenant_id", "user_id", "purpose", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "message_deliveries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("otp_challenge_id", sa.UUID(), nullable=False),
        sa.Column("delivery_no", sa.Integer(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_message_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status = 'queued' and completed_at is null and error_summary is null) or "
            "(status = 'sent' and completed_at is not null) or "
            "(status = 'failed' and completed_at is not null "
            "and error_summary is not null and error_summary <> '')",
            name=op.f("ck_message_deliveries__status_lifecycle"),
        ),
        sa.CheckConstraint("provider <> ''", name=op.f("ck_message_deliveries__provider_required")),
        sa.CheckConstraint(
            "status in ('queued', 'sent', 'failed')", name=op.f("ck_message_deliveries__status")
        ),
        sa.CheckConstraint(
            "delivery_no between 1 and 3", name=op.f("ck_message_deliveries__delivery_no_v1_range")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "otp_challenge_id"],
            ["otp_challenges.tenant_id", "otp_challenges.id"],
            name="fk_message_deliveries__tenant_otp_challenges",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], name="fk_message_deliveries__tenants"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message_deliveries")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_message_deliveries__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "otp_challenge_id",
            "delivery_no",
            name="uq_message_deliveries__tenant_challenge_delivery_no",
        ),
    )
    op.create_index(
        "ix_message_deliveries__tenant_challenge_created",
        "message_deliveries",
        ["tenant_id", "otp_challenge_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "otp_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("otp_challenge_id", sa.UUID(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "result in ('success', 'failed', 'locked', 'expired')",
            name=op.f("ck_otp_attempts__result"),
        ),
        sa.CheckConstraint(
            "attempt_no between 1 and 5", name=op.f("ck_otp_attempts__attempt_no_v1_range")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "otp_challenge_id"],
            ["otp_challenges.tenant_id", "otp_challenges.id"],
            name="fk_otp_attempts__tenant_otp_challenges",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_otp_attempts__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_otp_attempts")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_otp_attempts__tenant_id_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "otp_challenge_id",
            "attempt_no",
            name="uq_otp_attempts__tenant_challenge_attempt_no",
        ),
    )
    op.create_index(
        "ix_otp_attempts__tenant_challenge_created",
        "otp_attempts",
        ["tenant_id", "otp_challenge_id", sa.literal_column("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_otp_attempts__tenant_challenge_created", table_name="otp_attempts")
    op.drop_table("otp_attempts")
    op.drop_index(
        "ix_message_deliveries__tenant_challenge_created", table_name="message_deliveries"
    )
    op.drop_table("message_deliveries")
    op.drop_index("ix_otp_challenges__tenant_user_purpose_created", table_name="otp_challenges")
    op.drop_table("otp_challenges")
