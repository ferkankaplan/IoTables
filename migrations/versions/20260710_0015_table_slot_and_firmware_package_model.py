"""add table slot model and firmware package metadata

Revision ID: 20260710_0015
Revises: 20260706_0014
Create Date: 2026-07-10 00:00:00 UTC

Rollback note:
- Downgrade is only safe before the 100-slot venue model or one-time firmware
  package metadata is used. Existing table display claim rows are intentionally
  not preserved because the current model replaces claims with generated
  firmware package metadata.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0015"
down_revision: str | Sequence[str] | None = "20260706_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
TIMESTAMPTZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column("halls", sa.Column("table_number_base", sa.Integer(), nullable=True))
    op.execute("update halls set table_number_base = display_order * 100")
    op.alter_column("halls", "table_number_base", nullable=False)
    op.create_unique_constraint(
        "uq_halls__tenant_table_number_base",
        "halls",
        ["tenant_id", "table_number_base"],
    )
    op.create_check_constraint(
        op.f("ck_halls__table_number_base_range"),
        "halls",
        "table_number_base >= 100 and table_number_base % 100 = 0",
    )

    op.add_column("venue_tables", sa.Column("table_number", sa.Integer(), nullable=True))
    op.add_column("venue_tables", sa.Column("mode", sa.Text(), nullable=True))
    op.execute(
        """
        update venue_tables
        set
            table_number = halls.table_number_base + venue_tables.display_order - 1,
            mode = case
                when (halls.table_number_base + venue_tables.display_order - 1) % 100 in (0, 99)
                    then 'virtual_test'
                else 'physical'
            end
        from halls
        where venue_tables.tenant_id = halls.tenant_id
          and venue_tables.hall_id = halls.id
        """
    )
    _create_missing_table_slots()
    op.alter_column("venue_tables", "table_number", nullable=False)
    op.alter_column("venue_tables", "mode", nullable=False)
    op.create_unique_constraint(
        "uq_venue_tables__tenant_table_number",
        "venue_tables",
        ["tenant_id", "table_number"],
    )
    op.create_check_constraint(
        op.f("ck_venue_tables__mode"),
        "venue_tables",
        "mode in ('virtual_test', 'physical')",
    )
    op.create_check_constraint(
        op.f("ck_venue_tables__boundary_slots_virtual"),
        "venue_tables",
        "table_number % 100 not in (0, 99) or mode = 'virtual_test'",
    )

    op.drop_index(
        "ix_table_display_claims__tenant_table_created",
        table_name="table_display_claims",
    )
    op.drop_table("table_display_claims")
    op.create_table(
        "table_display_firmware_packages",
        sa.Column("id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("table_id", UUID, nullable=False),
        sa.Column("credential_id", UUID, nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("encrypted_firmware_ref", sa.Text(), nullable=False),
        sa.Column("download_token_hash", sa.Text(), nullable=False),
        sa.Column("generated_by_user_id", UUID, nullable=False),
        sa.Column("expires_at", TIMESTAMPTZ, nullable=False),
        sa.Column("downloaded_at", TIMESTAMPTZ),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_table_display_firmware_packages"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name="fk_table_display_firmware_packages__tenants",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "table_id"],
            ["venue_tables.tenant_id", "venue_tables.id"],
            name="fk_table_display_firmware_packages__tenant_venue_tables",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "credential_id"],
            ["table_display_credentials.tenant_id", "table_display_credentials.id"],
            name="fk_table_display_firmware_packages__tenant_credentials",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "generated_by_user_id"],
            ["users.tenant_id", "users.id"],
            name="fk_table_display_firmware_packages__tenant_users",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_table_display_firmware_packages__tenant_id_id",
        ),
        sa.UniqueConstraint(
            "download_token_hash",
            name="uq_table_display_firmware_packages__download_token_hash",
        ),
        sa.CheckConstraint(
            "downloaded_at is null or downloaded_at <= expires_at",
            name=op.f("ck_table_display_firmware_packages__downloaded_before_expiry"),
        ),
    )
    op.create_index(
        "ix_table_display_firmware_packages__tenant_table_created",
        "table_display_firmware_packages",
        ["tenant_id", "table_id", sa.text("created_at desc")],
    )
    op.create_index(
        "ix_table_display_firmware_packages__tenant_credential",
        "table_display_firmware_packages",
        ["tenant_id", "credential_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_table_display_firmware_packages__tenant_credential",
        table_name="table_display_firmware_packages",
    )
    op.drop_index(
        "ix_table_display_firmware_packages__tenant_table_created",
        table_name="table_display_firmware_packages",
    )
    op.drop_table("table_display_firmware_packages")
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

    op.drop_constraint(
        op.f("ck_venue_tables__boundary_slots_virtual"),
        "venue_tables",
        type_="check",
    )
    op.drop_constraint(op.f("ck_venue_tables__mode"), "venue_tables", type_="check")
    op.drop_constraint(
        "uq_venue_tables__tenant_table_number",
        "venue_tables",
        type_="unique",
    )
    op.drop_column("venue_tables", "mode")
    op.drop_column("venue_tables", "table_number")

    op.drop_constraint(op.f("ck_halls__table_number_base_range"), "halls", type_="check")
    op.drop_constraint("uq_halls__tenant_table_number_base", "halls", type_="unique")
    op.drop_column("halls", "table_number_base")


def _create_missing_table_slots() -> None:
    connection = op.get_bind()
    halls = connection.execute(
        sa.text(
            """
            select id, tenant_id, table_number_base
            from halls
            order by tenant_id, table_number_base
            """
        )
    ).mappings()
    now = datetime.now(UTC)
    for hall in halls:
        occupied_orders = {
            row["display_order"]
            for row in connection.execute(
                sa.text(
                    """
                    select display_order
                    from venue_tables
                    where tenant_id = :tenant_id and hall_id = :hall_id
                    """
                ),
                {"tenant_id": hall["tenant_id"], "hall_id": hall["id"]},
            ).mappings()
        }
        rows = []
        for offset in range(100):
            display_order = offset + 1
            if display_order in occupied_orders:
                continue
            table_number = hall["table_number_base"] + offset
            rows.append(
                {
                    "id": uuid4(),
                    "tenant_id": hall["tenant_id"],
                    "hall_id": hall["id"],
                    "table_number": table_number,
                    "name": f"Masa {table_number}",
                    "display_order": display_order,
                    "mode": "virtual_test",
                    "enabled": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        if rows:
            connection.execute(
                sa.text(
                    """
                    insert into venue_tables (
                        id,
                        tenant_id,
                        hall_id,
                        table_number,
                        name,
                        display_order,
                        mode,
                        enabled,
                        created_at,
                        updated_at
                    )
                    values (
                        :id,
                        :tenant_id,
                        :hall_id,
                        :table_number,
                        :name,
                        :display_order,
                        :mode,
                        :enabled,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                rows,
            )
