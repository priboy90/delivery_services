from __future__ import annotations

from alembic import op

revision = "0003_seed_parcel_types"
down_revision = "0002_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO parcel_types (id, name) VALUES
            (1, 'одежда'),
            (2, 'электроника'),
            (3, 'разное')
        ON CONFLICT (id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM parcel_types WHERE id IN (1,2,3);
        """
    )
