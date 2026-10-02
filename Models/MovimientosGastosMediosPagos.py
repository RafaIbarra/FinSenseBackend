from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship


from Config.settings import Base


class MovimientosGastosMediosPagos(Base):
    __tablename__ = "MovimientosGastosMediosPagos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    MontoMedio = Column("MontoMedio", Integer, nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    MovimientoGastoId = Column("MovimientoGastoId", Integer, ForeignKey("MovimientosGastos.Id"), nullable=False, index=True)
    MedioPagoUsuarioId = Column("MedioPagoUsuarioId", Integer, ForeignKey("MediosPagosUsuarios.Id"), nullable=False, index=True)
    CanalPagoId = Column("CanalPagoId", Integer, ForeignKey("CanalesPagos.Id"), nullable=True, index=True)

    movimiento_gasto = relationship("MovimientosGastos", back_populates="medios_pagos")
    medio_pago_usuario = relationship("MediosPagosUsuarios", back_populates="movimientos_gastos_medios_pagos")
    canal_pago = relationship("CanalesPagos", back_populates="movimientos_gastos_medios_pagos")
