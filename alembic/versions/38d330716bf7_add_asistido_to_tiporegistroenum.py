"""add_asistido_to_tiporegistroenum

Revision ID: 38d330716bf7
Revises: a663f83b5c64
Create Date: 2026-08-21 15:30:03.032785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38d330716bf7'
down_revision: Union[str, Sequence[str], None] = 'a663f83b5c64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tiporegistroenum ADD VALUE 'Asistido'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
