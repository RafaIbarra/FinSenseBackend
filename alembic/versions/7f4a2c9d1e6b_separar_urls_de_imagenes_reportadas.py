"""Separar URLs de imágenes reportadas

Revision ID: 7f4a2c9d1e6b
Revises: dc92a287f2f6
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f4a2c9d1e6b"
down_revision: Union[str, Sequence[str], None] = "dc92a287f2f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ImagenesReportadasUrls",
        sa.Column("Id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ImagenesReportadasId", sa.Integer(), nullable=False),
        sa.Column("CodigoReporte", sa.String(length=255), nullable=False),
        sa.Column("UrlImagen", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["ImagenesReportadasId"], ["ImagenesReportadas.Id"]),
        sa.PrimaryKeyConstraint("Id"),
        sa.UniqueConstraint("UrlImagen"),
    )
    op.create_index(
        "ix_ImagenesReportadasUrls_Id",
        "ImagenesReportadasUrls",
        ["Id"],
        unique=False,
    )
    op.create_index(
        "ix_ImagenesReportadasUrls_ImagenesReportadasId",
        "ImagenesReportadasUrls",
        ["ImagenesReportadasId"],
        unique=False,
    )
    op.create_index(
        "ix_ImagenesReportadasUrls_CodigoReporte",
        "ImagenesReportadasUrls",
        ["CodigoReporte"],
        unique=False,
    )
    op.create_index(
        "ix_ImagenesReportadasUrls_UrlImagen",
        "ImagenesReportadasUrls",
        ["UrlImagen"],
        unique=True,
    )

    op.execute(
        sa.text(
            'INSERT INTO "ImagenesReportadasUrls" '
            '("ImagenesReportadasId", "CodigoReporte", "UrlImagen") '
            'SELECT "Id", "CodigoReporte", "UrlImagen" FROM "ImagenesReportadas"'
        )
    )

    op.drop_index("ix_ImagenesReportadas_CodigoReporte", table_name="ImagenesReportadas")
    op.drop_index("ix_ImagenesReportadas_UrlImagen", table_name="ImagenesReportadas")
    op.drop_column("ImagenesReportadas", "CodigoReporte")
    op.drop_column("ImagenesReportadas", "UrlImagen")


def downgrade() -> None:
    op.add_column(
        "ImagenesReportadas",
        sa.Column("CodigoReporte", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "ImagenesReportadas",
        sa.Column("UrlImagen", sa.String(length=500), nullable=True),
    )
    op.execute(
        sa.text(
            'UPDATE "ImagenesReportadas" AS reporte SET '
            '"CodigoReporte" = detalle."CodigoReporte", '
            '"UrlImagen" = detalle."UrlImagen" '
            'FROM (SELECT DISTINCT ON ("ImagenesReportadasId") '
            '"ImagenesReportadasId", "CodigoReporte", "UrlImagen" '
            'FROM "ImagenesReportadasUrls" ORDER BY "ImagenesReportadasId", "Id") AS detalle '
            'WHERE reporte."Id" = detalle."ImagenesReportadasId"'
        )
    )
    op.alter_column("ImagenesReportadas", "CodigoReporte", nullable=False)
    op.alter_column("ImagenesReportadas", "UrlImagen", nullable=False)
    op.create_index(
        "ix_ImagenesReportadas_CodigoReporte",
        "ImagenesReportadas",
        ["CodigoReporte"],
        unique=False,
    )
    op.create_index(
        "ix_ImagenesReportadas_UrlImagen",
        "ImagenesReportadas",
        ["UrlImagen"],
        unique=True,
    )

    op.drop_index("ix_ImagenesReportadasUrls_UrlImagen", table_name="ImagenesReportadasUrls")
    op.drop_index("ix_ImagenesReportadasUrls_CodigoReporte", table_name="ImagenesReportadasUrls")
    op.drop_index("ix_ImagenesReportadasUrls_ImagenesReportadasId", table_name="ImagenesReportadasUrls")
    op.drop_index("ix_ImagenesReportadasUrls_Id", table_name="ImagenesReportadasUrls")
    op.drop_table("ImagenesReportadasUrls")
