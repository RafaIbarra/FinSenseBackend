"""creacion de tabla para envio de correos

Revision ID: 1a6ed9fbb0f3
Revises: 6a51b30cc6d0
Create Date: 2026-09-01 23:05:23.817202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a6ed9fbb0f3'
down_revision: Union[str, Sequence[str], None] = '6a51b30cc6d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
