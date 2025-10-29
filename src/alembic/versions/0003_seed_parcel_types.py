# FILE: src/alembic/versions/0003_seed_parcel_types.py
from __future__ import annotations

from alembic import op

# Идентификаторы ревизий
revision = "0003_seed_parcel_types"
down_revision = "0002_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Сидим 3 типа посылок; если уже есть — пропускаем
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
    # Откатим только те, что с этими id (не трогаем пользовательские)
    op.execute(
        """
        DELETE FROM parcel_types WHERE id IN (1,2,3);
        """
    )
