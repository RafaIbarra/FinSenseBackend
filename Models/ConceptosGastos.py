from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class ConceptosGastos(Base):
	__tablename__ = "ConceptosGastos"

	Id = Column("Id", Integer, primary_key=True, index=True)
	NombreConcepto = Column("NombreConcepto", String(200), nullable=False)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

	movimientos_gastos_conceptos = relationship(
		"MovimientosGastosConceptos",
		back_populates="concepto",
		cascade="all, delete-orphan",
	)
