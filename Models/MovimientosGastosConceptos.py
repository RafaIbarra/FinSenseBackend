from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class MovimientosGastosConceptos(Base):
	__tablename__ = "MovimientosGastosConceptos"
	__table_args__ = (
		UniqueConstraint("MovimientoGastoId", "ConceptoId", name="uq_movimiento_gasto_concepto"),
	)

	Id = Column("Id", Integer, primary_key=True, index=True)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
	MovimientoGastoId = Column(
		"MovimientoGastoId", Integer, ForeignKey("MovimientosGastos.Id"), nullable=False, index=True
	)
	ConceptoId = Column("ConceptoId", Integer, ForeignKey("ConceptosGastos.Id"), nullable=False, index=True)

	movimiento_gasto = relationship("MovimientosGastos", back_populates="conceptos")
	concepto = relationship("ConceptosGastos", back_populates="movimientos_gastos_conceptos")
