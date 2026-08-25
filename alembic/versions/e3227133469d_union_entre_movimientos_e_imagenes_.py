"""union entre movimientos e imagenes pendientes

Revision ID: e3227133469d
Revises: 38d330716bf7
Create Date: 2026-08-21 19:32:10.531312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3227133469d'
down_revision: Union[str, Sequence[str], None] = '38d330716bf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
