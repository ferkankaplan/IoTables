"""create governance foundation

Revision ID: 20260702_0007
Revises: 20260702_0006
Create Date: 2026-07-02 18:18:27.731099+00:00

Rollback note:
- Safe to downgrade only before audit events, outbox messages, or external
  effect attempt records exist. After use, dropping these tables requires
  explicit operational/security/audit data-retention approval.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260702_0007"
down_revision: str | Sequence[str] | None = "20260702_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("effect_type", sa.Text(), nullable=False),
        sa.Column("aggregate_type", sa.Text(), nullable=False),
        sa.Column("aggregate_id", sa.Text(), nullable=False),
        sa.Column("payload_ref", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("idempotency_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_by", sa.Text(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(status = 'claimed' and claimed_by is not null and claimed_by <> '' "
            "and claimed_at is not null and claim_expires_at is not null "
            "and completed_at is null) or "
            "(status <> 'claimed' and claimed_by is null "
            "and claimed_at is null and claim_expires_at is null)",
            name=op.f("ck_outbox_messages__claim_lifecycle"),
        ),
        sa.CheckConstraint(
            "(status = 'completed' and completed_at is not null) or "
            "(status <> 'completed' and completed_at is null)",
            name=op.f("ck_outbox_messages__completed_lifecycle"),
        ),
        sa.CheckConstraint(
            "aggregate_id <> ''", name=op.f("ck_outbox_messages__aggregate_id_required")
        ),
        sa.CheckConstraint(
            "aggregate_type <> ''", name=op.f("ck_outbox_messages__aggregate_type_required")
        ),
        sa.CheckConstraint(
            "effect_type in ('sms', 'printer', 'fiscal', 'payment_provider', "
            "'dns', 'notification', 'device')",
            name=op.f("ck_outbox_messages__effect_type"),
        ),
        sa.CheckConstraint(
            "idempotency_ref <> ''", name=op.f("ck_outbox_messages__idempotency_ref_required")
        ),
        sa.CheckConstraint(
            "jsonb_typeof(payload_ref) = 'object'",
            name=op.f("ck_outbox_messages__payload_ref_object"),
        ),
        sa.CheckConstraint(
            "status in ('pending', 'claimed', 'completed', 'failed')",
            name=op.f("ck_outbox_messages__status"),
        ),
        sa.CheckConstraint(
            "claim_expires_at is null or "
            "(claimed_at is not null and claim_expires_at > claimed_at)",
            name=op.f("ck_outbox_messages__claim_expiry_after_claim"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_outbox_messages__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox_messages")),
        sa.UniqueConstraint(
            "effect_type", "idempotency_ref", name="uq_outbox_messages__effect_idempotency_ref"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_outbox_messages__tenant_id_id"),
    )
    op.create_index(
        "ix_outbox_messages__aggregate",
        "outbox_messages",
        ["aggregate_type", "aggregate_id"],
        unique=False,
    )
    op.create_index(
        "ix_outbox_messages__status_next_attempt",
        "outbox_messages",
        ["status", "next_attempt_at", "claim_expires_at", "created_at"],
        unique=False,
        postgresql_where=sa.text("status IN ('pending', 'failed', 'claimed')"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action in ('platform_owner.created', 'platform_owner.totp_enrolled', "
            "'tenant.created', 'tenant.provisioning_failed', 'tenant.activated', "
            "'tenant.suspended', 'tenant.gsm_changed', 'starter_template.applied', "
            "'user.created', 'user.disabled', 'password.changed', 'otp.verified', "
            "'table_display.provisioned', 'table_display.revoked', "
            "'order.submitted', 'preparation.status_changed', "
            "'delivery.status_changed', 'payment.recorded', 'payment.voided', "
            "'session.closed', 'cashier.correction_applied')",
            name=op.f("ck_audit_events__action"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(metadata) = 'object'", name=op.f("ck_audit_events__metadata_object")
        ),
        sa.CheckConstraint(
            "reason is null or reason <> ''", name=op.f("ck_audit_events__reason_not_empty")
        ),
        sa.CheckConstraint("target_id <> ''", name=op.f("ck_audit_events__target_id_required")),
        sa.CheckConstraint("target_type <> ''", name=op.f("ck_audit_events__target_type_required")),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_audit_events__users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name="fk_audit_events__tenants"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_audit_events__tenant_id_id"),
    )
    op.create_index(
        "ix_audit_events__action_created",
        "audit_events",
        ["action", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_audit_events__target",
        "audit_events",
        ["target_type", "target_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix_audit_events__tenant_created",
        "audit_events",
        ["tenant_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "external_effect_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("outbox_message_id", sa.UUID(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "(result = 'success' and completed_at is not null) or "
            "(result <> 'success' and completed_at is not null "
            "and result_summary is not null and result_summary <> '')",
            name=op.f("ck_external_effect_attempts__result_lifecycle"),
        ),
        sa.CheckConstraint(
            "result in ('success', 'retryable_failure', 'permanent_failure', 'timeout')",
            name=op.f("ck_external_effect_attempts__result"),
        ),
        sa.CheckConstraint(
            "attempt_no > 0", name=op.f("ck_external_effect_attempts__attempt_no_positive")
        ),
        sa.ForeignKeyConstraint(
            ["outbox_message_id"],
            ["outbox_messages.id"],
            name="fk_external_effect_attempts__outbox_messages",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_external_effect_attempts")),
        sa.UniqueConstraint(
            "outbox_message_id",
            "attempt_no",
            name="uq_external_effect_attempts__message_attempt_no",
        ),
    )
    op.create_index(
        "ix_external_effect_attempts__message_started",
        "external_effect_attempts",
        ["outbox_message_id", sa.literal_column("started_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_external_effect_attempts__message_started", table_name="external_effect_attempts"
    )
    op.drop_table("external_effect_attempts")
    op.drop_index("ix_audit_events__tenant_created", table_name="audit_events")
    op.drop_index("ix_audit_events__target", table_name="audit_events")
    op.drop_index("ix_audit_events__action_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index(
        "ix_outbox_messages__status_next_attempt",
        table_name="outbox_messages",
        postgresql_where=sa.text("status IN ('pending', 'failed', 'claimed')"),
    )
    op.drop_index("ix_outbox_messages__aggregate", table_name="outbox_messages")
    op.drop_table("outbox_messages")
