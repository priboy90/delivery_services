from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parcel_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
    )

    op.create_table(
        "parcels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Text(), nullable=False),
        # session_public_id добавим в 0004, чтобы сохранить обратную совместимость апгрейда
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(10, 3), nullable=False),
        sa.Column(
            "type_id",
            sa.Integer(),
            sa.ForeignKey("parcel_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("cost_rub", sa.Numeric(18, 2), nullable=True),
        sa.Column("shipping_company_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index("ix_parcels_session_id", "parcels", ["session_id"])
    op.create_index("ix_parcels_type_id", "parcels", ["type_id"])

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_parcels_unbound
        ON parcels (shipping_company_id)
        WHERE shipping_company_id IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_parcels_unbound")
    op.drop_index("ix_parcels_type_id", table_name="parcels")
    op.drop_index("ix_parcels_session_id", table_name="parcels")
    op.drop_table("parcels")
    op.drop_table("parcel_types")
