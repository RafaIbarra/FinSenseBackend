from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship


from Config.settings import Base


class CanalesPagos(Base):
    __tablename__ = "CanalesPagos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreCanal = Column("NombreCanal", String(200), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

    movimientos_gastos_medios_pagos = relationship(
        "MovimientosGastosMediosPagos",
        back_populates="canal_pago",
    )