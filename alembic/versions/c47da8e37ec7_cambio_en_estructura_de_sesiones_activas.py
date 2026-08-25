"""cambio en estructura de sesiones activas

Revision ID: c47da8e37ec7
Revises: 391983d916c9
Create Date: 2026-08-25 00:16:05.323837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c47da8e37ec7'
down_revision: Union[str, Sequence[str], None] = '391983d916c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
