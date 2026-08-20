from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class CategoriasGastos(Base):
    __tablename__ = "CategoriasGastos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreCategoria = Column("NombreCategoria", String(200), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    movimientos_gastos = relationship(
        "MovimientosGastos",
        back_populates="categoria",
        cascade="all, delete-orphan",
    )
