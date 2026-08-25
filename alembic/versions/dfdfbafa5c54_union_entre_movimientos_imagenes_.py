"""union_entre_movimientos_imagenes_pendientes

Revision ID: dfdfbafa5c54
Revises: e3227133469d
Create Date: 2026-08-21 19:33:00.964476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfdfbafa5c54'
down_revision: Union[str, Sequence[str], None] = 'e3227133469d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
