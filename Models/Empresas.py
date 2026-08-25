from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class Empresas(Base):
    __tablename__ = "Empresas"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreEmpresa = Column("NombreEmpresa", String(200), nullable=False)
    Rubro = Column("Rubro", String(200), nullable=True)
    Ruc = Column("Ruc", String(50), nullable=False, unique=True, index=True)
    UrlLogo = Column("UrlLogo", String(255), nullable=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

    movimientos_gastos = relationship(
        "MovimientosGastos",
        back_populates="empresa",
        cascade="all, delete-orphan",
    )
