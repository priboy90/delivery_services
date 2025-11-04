from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_init"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "parcels",
        "created_at",
        existing_type=sa.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "parcels",
        "created_at",
        existing_type=sa.TIMESTAMP(timezone=True),
        server_default=sa.text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
