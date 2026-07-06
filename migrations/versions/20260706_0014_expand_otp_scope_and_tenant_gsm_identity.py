"""expand otp scope and tenant gsm identity

Revision ID: 20260706_0014
Revises: 20260705_0013
Create Date: 2026-07-06 14:20:00.000000+03:00

Rollback note:
- Downgrade is only safe before platform-scoped tenant creation OTP challenges
  exist and before tenant GSM uniqueness has been relied on for password reset
  proof. Platform-scoped OTP rows must be removed or retained outside this
  schema before restoring the old tenant-only OTP constraints.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260706_0014"
down_revision: str | Sequence[str] | None = "20260705_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_PURPOSES = "'tenant_admin_first_password', 'cashier_first_password'"
NEW_PURPOSES = (
    "'tenant_creation', 'staff_password_reset', "
    "'tenant_admin_first_password', 'cashier_first_password'"
)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM tenants
                GROUP BY gsm_number
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'duplicate tenant gsm_number values must be resolved before 20260706_0014';
            END IF;
        END $$;
        """
    )
    op.create_index("uq_tenants__gsm_number", "tenants", ["gsm_number"], unique=True)

    op.drop_constraint(
        op.f("fk_otp_challenges__tenant_users"),
        "otp_challenges",
        type_="foreignkey",
    )
    op.drop_constraint(op.f("ck_otp_challenges__purpose"), "otp_challenges", type_="check")
    op.alter_column("otp_challenges", "tenant_id", nullable=True)
    op.create_foreign_key(
        "fk_otp_challenges__users",
        "otp_challenges",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_otp_challenges__tenant_users",
        "otp_challenges",
        "users",
        ["tenant_id", "user_id"],
        ["tenant_id", "id"],
    )
    op.create_check_constraint(
        op.f("ck_otp_challenges__purpose"),
        "otp_challenges",
        f"purpose in ({NEW_PURPOSES})",
    )
    op.create_check_constraint(
        op.f("ck_otp_challenges__tenant_scope"),
        "otp_challenges",
        "(purpose = 'tenant_creation' and tenant_id is null) or "
        "(purpose <> 'tenant_creation' and tenant_id is not null)",
    )

    op.drop_constraint(
        op.f("fk_otp_attempts__tenant_otp_challenges"), "otp_attempts", type_="foreignkey"
    )
    op.alter_column("otp_attempts", "tenant_id", nullable=True)
    op.create_foreign_key(
        "fk_otp_attempts__otp_challenges",
        "otp_attempts",
        "otp_challenges",
        ["otp_challenge_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_otp_attempts__tenant_otp_challenges",
        "otp_attempts",
        "otp_challenges",
        ["tenant_id", "otp_challenge_id"],
        ["tenant_id", "id"],
    )

    op.drop_constraint(
        op.f("fk_message_deliveries__tenant_otp_challenges"),
        "message_deliveries",
        type_="foreignkey",
    )
    op.alter_column("message_deliveries", "tenant_id", nullable=True)
    op.create_foreign_key(
        "fk_message_deliveries__otp_challenges",
        "message_deliveries",
        "otp_challenges",
        ["otp_challenge_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_message_deliveries__tenant_otp_challenges",
        "message_deliveries",
        "otp_challenges",
        ["tenant_id", "otp_challenge_id"],
        ["tenant_id", "id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_message_deliveries__otp_challenges"),
        "message_deliveries",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_message_deliveries__tenant_otp_challenges"),
        "message_deliveries",
        type_="foreignkey",
    )
    op.alter_column("message_deliveries", "tenant_id", nullable=False)
    op.create_foreign_key(
        "fk_message_deliveries__tenant_otp_challenges",
        "message_deliveries",
        "otp_challenges",
        ["tenant_id", "otp_challenge_id"],
        ["tenant_id", "id"],
    )

    op.drop_constraint(
        op.f("fk_otp_attempts__otp_challenges"), "otp_attempts", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_otp_attempts__tenant_otp_challenges"), "otp_attempts", type_="foreignkey"
    )
    op.alter_column("otp_attempts", "tenant_id", nullable=False)
    op.create_foreign_key(
        "fk_otp_attempts__tenant_otp_challenges",
        "otp_attempts",
        "otp_challenges",
        ["tenant_id", "otp_challenge_id"],
        ["tenant_id", "id"],
    )

    op.drop_constraint(op.f("ck_otp_challenges__tenant_scope"), "otp_challenges", type_="check")
    op.drop_constraint(op.f("ck_otp_challenges__purpose"), "otp_challenges", type_="check")
    op.drop_constraint(
        op.f("fk_otp_challenges__tenant_users"),
        "otp_challenges",
        type_="foreignkey",
    )
    op.drop_constraint(op.f("fk_otp_challenges__users"), "otp_challenges", type_="foreignkey")
    op.alter_column("otp_challenges", "tenant_id", nullable=False)
    op.create_foreign_key(
        "fk_otp_challenges__tenant_users",
        "otp_challenges",
        "users",
        ["tenant_id", "user_id"],
        ["tenant_id", "id"],
    )
    op.create_check_constraint(
        op.f("ck_otp_challenges__purpose"),
        "otp_challenges",
        f"purpose in ({OLD_PURPOSES})",
    )

    op.drop_index("uq_tenants__gsm_number", table_name="tenants")
