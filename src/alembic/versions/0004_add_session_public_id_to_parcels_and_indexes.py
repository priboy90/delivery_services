from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_add_session_public_id"
down_revision = "0003_seed_parcel_types"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("parcels", sa.Column("session_public_id", sa.String(length=32), nullable=True))

    op.execute(
        """
        UPDATE parcels
        SET session_public_id = LOWER(SUBSTRING(md5(session_id || ':' || id) FOR 16))
        WHERE session_public_id IS NULL
        """
    )

    op.alter_column("parcels", "session_public_id", nullable=False)

    op.create_index("ix_parcels_session_public_id", "parcels", ["session_public_id"])
    op.create_unique_constraint("uq_parcels_session_public", "parcels", ["session_id", "session_public_id"])


def downgrade():
    op.drop_constraint("uq_parcels_session_public", "parcels", type_="unique")
    op.drop_index("ix_parcels_session_public_id", table_name="parcels")
    op.drop_column("parcels", "session_public_id")
