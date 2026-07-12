"""expand first password otp purposes

Revision ID: 20260712_0016
Revises: 20260710_0015
Create Date: 2026-07-12 00:00:00 UTC

Rollback note:
- Downgrade is only safe before station/service first-password OTP challenges
  are created. Existing challenges with the new purposes must be completed,
  deleted, or archived before restoring the older purpose constraint.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260712_0016"
down_revision: str | Sequence[str] | None = "20260710_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_PURPOSES = (
    "'tenant_creation', 'staff_password_reset', "
    "'tenant_admin_first_password', 'cashier_first_password'"
)
NEW_PURPOSES = (
    "'tenant_creation', 'staff_password_reset', "
    "'tenant_admin_first_password', 'cashier_first_password', "
    "'station_staff_first_password', 'service_staff_first_password'"
)


def upgrade() -> None:
    op.drop_constraint(op.f("ck_otp_challenges__purpose"), "otp_challenges", type_="check")
    op.create_check_constraint(
        op.f("ck_otp_challenges__purpose"),
        "otp_challenges",
        f"purpose in ({NEW_PURPOSES})",
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM otp_challenges
                WHERE purpose in ('station_staff_first_password', 'service_staff_first_password')
            ) THEN
                RAISE EXCEPTION
                    'new first-password OTP challenges must be removed before downgrade';
            END IF;
        END $$;
        """
    )
    op.drop_constraint(op.f("ck_otp_challenges__purpose"), "otp_challenges", type_="check")
    op.create_check_constraint(
        op.f("ck_otp_challenges__purpose"),
        "otp_challenges",
        f"purpose in ({OLD_PURPOSES})",
    )
