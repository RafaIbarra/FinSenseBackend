"""cambiar FK por CodigoTarea en errores de imagenes pendientes

Revision ID: 7b2c9d4e1f6a
Revises: 316608371b88
Create Date: 2026-09-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b2c9d4e1f6a"
down_revision: Union[str, Sequence[str], None] = "316608371b88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = "ErroresProcesamientoImagenesPendientes"
FK_COLUMN = "ImagenesPendientesId"
# El nombre original ("..._ImagenesPendientesId_fkey") tiene 64 caracteres,
# uno mas del limite de 63 de PostgreSQL. Usamos un nombre corto propio
# para cuando la recreamos en el downgrade.
FK_NAME = "fk_errores_proc_img_pend_imagenes_pendientes_id"


def _find_fk_name(conn, table_name: str, column_name: str) -> Union[str, None]:
    """Busca en la base el nombre REAL de la FK sobre esa columna.

    No confiamos en el nombre escrito a mano porque, si ya excedia el
    limite de 63 caracteres al crearla, Postgres/SQLAlchemy pudo haberla
    guardado truncada (o con otro nombre) en su momento.
    """
    inspector = sa.inspect(conn)
    for fk in inspector.get_foreign_keys(table_name):
        if fk.get("constrained_columns") == [column_name]:
            return fk.get("name")
    return None


def upgrade() -> None:
    conn = op.get_bind()
    fk_name = _find_fk_name(conn, TABLE_NAME, FK_COLUMN)

    op.drop_index(
        "ix_ErroresProcesamientoImagenesPendientes_ImagenesPendientesId",
        table_name=TABLE_NAME,
    )
    if fk_name:
        op.drop_constraint(fk_name, TABLE_NAME, type_="foreignkey")
    op.drop_column(TABLE_NAME, FK_COLUMN)
    op.add_column(
        TABLE_NAME,
        sa.Column("CodigoTarea", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_ErroresProcesamientoImagenesPendientes_CodigoTarea",
        TABLE_NAME,
        ["CodigoTarea"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ErroresProcesamientoImagenesPendientes_CodigoTarea",
        TABLE_NAME,
        type_="unique",
    )
    op.drop_column(TABLE_NAME, "CodigoTarea")
    op.add_column(
        TABLE_NAME,
        sa.Column(FK_COLUMN, sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        FK_NAME,
        TABLE_NAME,
        "ImagenesPendientes",
        [FK_COLUMN],
        ["Id"],
    )
    op.create_index(
        "ix_ErroresProcesamientoImagenesPendientes_ImagenesPendientesId",
        TABLE_NAME,
        [FK_COLUMN],
        unique=False,
    )