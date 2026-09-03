import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Enum as SQLEnum, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class EstadoResolucionEnum(enum.Enum):
	Pendiente = "Pendiente"
	Resuelto = "Resuelto"


class ImagenesReportadas(Base):
	__tablename__ = "ImagenesReportadas"

	Id = Column("Id", Integer, primary_key=True, autoincrement=True, index=True)
	CodigoReporte = Column("CodigoReporte", String(255), nullable=False, index=True)
	UrlImagen = Column("UrlImagen", String(500), nullable=False, unique=True, index=True)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
	UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
	Respuesta = Column("Respuesta", JSON, nullable=True)
	Observacion = Column("Observacion", String(1000), nullable=True)
	EstadoResolucion = Column(
		"EstadoResolucion",
		SQLEnum(EstadoResolucionEnum, name="estadoresolucionenum"),
		nullable=False,
		default=EstadoResolucionEnum.Pendiente,
	)
	Resolucion = Column("Resolucion", String(1000), nullable=True)
	FechaResolucion = Column("FechaResolucion", DateTime(timezone=True), nullable=True)

	usuario = relationship("Usuarios", back_populates="imagenes_reportadas")
