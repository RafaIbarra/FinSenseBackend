"""agregar valor Procesada a estadoestadisticaenum

Revision ID: a6f6bf8014f6
Revises: 1055816ad81b
Create Date: 2026-09-14 00:47:13.940792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6f6bf8014f6'
down_revision: Union[str, Sequence[str], None] = '1055816ad81b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TYPE estadoestadisticaenum ADD VALUE IF NOT EXISTS 'Procesada'")


def downgrade():
    # Postgres no permite quitar un valor de un ENUM directamente.
    pass