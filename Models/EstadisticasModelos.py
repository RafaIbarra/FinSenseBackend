import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class OrigenEstadisticaEnum(enum.Enum):
    Aplicacion = "Aplicacion"
    Jobs = "Jobs"


class EstadoEstadisticaEnum(enum.Enum):
    Pendiente = "Pendiente"
    Registrada = "Registrada"
    Descartada = "Descartada"



class EstadisticasModelos(Base):
    __tablename__ = "EstadisticasModelos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    Origen = Column("Origen", SQLEnum(OrigenEstadisticaEnum, name="origenestadisticaenum"), nullable=False)
    Estado = Column("Estado", SQLEnum(EstadoEstadisticaEnum, name="estadoestadisticaenum"), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuarios", back_populates="estadisticas_modelos")
    detalles = relationship(
        "EstadisticasModelosDetalle",
        back_populates="estadistica_modelo",
        cascade="all, delete-orphan",
    )
    imagenes = relationship(
        "EstadisticasModelosImagenes",
        back_populates="estadistica_modelo",
        cascade="all, delete-orphan",
    )