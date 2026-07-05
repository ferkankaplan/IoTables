"""remove tenant-level DNS readiness

Revision ID: 20260705_0013
Revises: 20260703_0012
Create Date: 2026-07-05 22:00:00.000000+00:00

Rollback note:
- Safe to downgrade only before code depends on the removal of tenant-level
  DNS readiness. Downgrade recreates the old columns as `false` because the
  previous per-tenant readiness state is intentionally discarded.
- Upgrade expects no historical `tenant.dns_ready_changed` audit events. If
  such events exist, stop and decide whether to retain a legacy audit catalog
  or remap records explicitly before applying this migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260705_0013"
down_revision: str | Sequence[str] | None = "20260703_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_ACTIONS = (
    "'platform_owner.created', 'platform_owner.totp_enrolled', "
    "'tenant.created', 'tenant.provisioning_failed', 'tenant.activated', "
    "'tenant.suspended', 'tenant.gsm_changed', 'tenant.profile_updated', "
    "'tenant.dns_ready_changed', 'starter_template.applied', "
    "'user.created', 'user.disabled', 'password.changed', 'otp.verified', "
    "'venue_layout.changed', 'table.disabled', "
    "'station.changed', 'station.disabled', "
    "'menu_catalog.changed', 'availability.changed', "
    "'table_display.provisioned', 'table_display.revoked', 'order.submitted', "
    "'preparation.status_changed', 'delivery.status_changed', "
    "'payment.recorded', 'payment.voided', 'session.closed', "
    "'cashier.correction_applied'"
)

NEW_ACTIONS = (
    "'platform_owner.created', 'platform_owner.totp_enrolled', "
    "'tenant.created', 'tenant.provisioning_failed', 'tenant.activated', "
    "'tenant.suspended', 'tenant.gsm_changed', 'tenant.profile_updated', "
    "'starter_template.applied', "
    "'user.created', 'user.disabled', 'password.changed', 'otp.verified', "
    "'venue_layout.changed', 'table.disabled', "
    "'station.changed', 'station.disabled', "
    "'menu_catalog.changed', 'availability.changed', "
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
    op.drop_column("tenant_health", "dns_ready")
    op.drop_column("tenants", "dns_ready")


def downgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("dns_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tenants", "dns_ready", server_default=None)
    op.add_column(
        "tenant_health",
        sa.Column("dns_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tenant_health", "dns_ready", server_default=None)
    op.drop_constraint(op.f("ck_audit_events__action"), "audit_events", type_="check")
    op.create_check_constraint(
        op.f("ck_audit_events__action"),
        "audit_events",
        f"action in ({OLD_ACTIONS})",
    )
