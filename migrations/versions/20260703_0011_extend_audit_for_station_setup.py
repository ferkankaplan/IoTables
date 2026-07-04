"""extend audit catalog for station setup

Revision ID: 20260703_0011
Revises: 20260703_0010
Create Date: 2026-07-03 12:30:00.000000+00:00

Rollback note:
- Safe to downgrade only before station setup audit events are written.
  After use, downgrading requires retaining or remapping `station.changed`
  and `station.disabled` events before restoring the previous constraint.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260703_0011"
down_revision: str | Sequence[str] | None = "20260703_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_ACTIONS = (
    "'platform_owner.created', 'platform_owner.totp_enrolled', "
    "'tenant.created', 'tenant.provisioning_failed', 'tenant.activated', "
    "'tenant.suspended', 'tenant.gsm_changed', 'tenant.profile_updated', "
    "'tenant.dns_ready_changed', 'starter_template.applied', "
    "'user.created', 'user.disabled', 'password.changed', 'otp.verified', "
    "'venue_layout.changed', 'table.disabled', "
    "'table_display.provisioned', 'table_display.revoked', 'order.submitted', "
    "'preparation.status_changed', 'delivery.status_changed', "
    "'payment.recorded', 'payment.voided', 'session.closed', "
    "'cashier.correction_applied'"
)

NEW_ACTIONS = (
    "'platform_owner.created', 'platform_owner.totp_enrolled', "
    "'tenant.created', 'tenant.provisioning_failed', 'tenant.activated', "
    "'tenant.suspended', 'tenant.gsm_changed', 'tenant.profile_updated', "
    "'tenant.dns_ready_changed', 'starter_template.applied', "
    "'user.created', 'user.disabled', 'password.changed', 'otp.verified', "
    "'venue_layout.changed', 'table.disabled', "
    "'station.changed', 'station.disabled', "
    "'table_display.provisioned', 'table_display.revoked', 'order.submitted', "
    "'preparation.status_changed', 'delivery.status_changed', "
    "'payment.recorded', 'payment.voided', 'session.closed', "
    "'cashier.correction_applied'"
)


def upgrade() -> None:
    op.drop_constraint(op.f("ck_audit_events__action"), "audit_events", type_="check")
    op.create_check_constraint(
        op.f("ck_audit_events__action"),
        "audit_events",
        f"action in ({NEW_ACTIONS})",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_audit_events__action"), "audit_events", type_="check")
    op.create_check_constraint(
        op.f("ck_audit_events__action"),
        "audit_events",
        f"action in ({OLD_ACTIONS})",
    )
