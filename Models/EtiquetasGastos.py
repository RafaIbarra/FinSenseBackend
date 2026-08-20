from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class EtiquetasGastos(Base):
	__tablename__ = "EtiquetasGastos"

	Id = Column("Id", Integer, primary_key=True, index=True)
	NombreEtiqueta = Column("NombreEtiqueta", String(200), nullable=False)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

	movimientos_gastos_etiquetas = relationship(
		"MovimientosGastosEtiquetas",
		back_populates="etiqueta",
		cascade="all, delete-orphan",
	)
