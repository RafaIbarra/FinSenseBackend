from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class MovimientosGastosImagenes(Base):
    __tablename__ = "MovimientosGastosImagenes"

    Id = Column("Id", Integer, primary_key=True, index=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    UrlImagen = Column("UrlImagen", String(255), nullable=True)
    ReferenciaCola = Column("ReferenciaCola", String(255), nullable=True)
    MovimientoGastoId = Column("MovimientoGastoId", Integer, ForeignKey("MovimientosGastos.Id"), nullable=False, index=True)

    movimiento_gasto = relationship("MovimientosGastos", back_populates="imagenes")
