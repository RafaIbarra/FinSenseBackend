from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class MovimientosGastosEtiquetas(Base):
	__tablename__ = "MovimientosGastosEtiquetas"
	__table_args__ = (
		UniqueConstraint("MovimientoGastoId", "EtiquetaId", name="uq_movimiento_gasto_etiqueta"),
	)

	Id = Column("Id", Integer, primary_key=True, index=True)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
	MovimientoGastoId = Column(
		"MovimientoGastoId", Integer, ForeignKey("MovimientosGastos.Id"), nullable=False, index=True
	)
	EtiquetaId = Column("EtiquetaId", Integer, ForeignKey("EtiquetasGastos.Id"), nullable=False, index=True)

	movimiento_gasto = relationship("MovimientosGastos", back_populates="etiquetas")
	etiqueta = relationship("EtiquetasGastos", back_populates="movimientos_gastos_etiquetas")
