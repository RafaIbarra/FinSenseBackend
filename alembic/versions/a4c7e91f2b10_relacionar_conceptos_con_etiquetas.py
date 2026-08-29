"""relacionar conceptos con etiquetas

Revision ID: a4c7e91f2b10
Revises: 9233191359be
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4c7e91f2b10"
down_revision: Union[str, Sequence[str], None] = "9233191359be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "MovimientosGastosConceptos",
        sa.Column("EtiquetaId", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_MovimientosGastosConceptos_EtiquetaId"),
        "MovimientosGastosConceptos",
        ["EtiquetaId"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("MovimientosGastosConceptos_EtiquetaId_fkey"),
        "MovimientosGastosConceptos",
        "EtiquetasGastos",
        ["EtiquetaId"],
        ["Id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("MovimientosGastosConceptos_EtiquetaId_fkey"),
        "MovimientosGastosConceptos",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_MovimientosGastosConceptos_EtiquetaId"),
        table_name="MovimientosGastosConceptos",
    )
    op.drop_column("MovimientosGastosConceptos", "EtiquetaId")
