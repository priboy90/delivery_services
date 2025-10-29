# FILE: src/alembic/versions/0002_init.py
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_init"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    # приведение server_default к now() (PostgreSQL)
    op.alter_column(
        "parcels",
        "created_at",
        existing_type=sa.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def downgrade():
    # откат server_default
    op.alter_column(
        "parcels",
        "created_at",
        existing_type=sa.TIMESTAMP(timezone=True),
        server_default=sa.text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
