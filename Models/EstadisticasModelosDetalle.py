import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class TipoOperacionEnum(enum.Enum):
    Extraccion = "Extraccion"
    Clasificacion = "Clasificacion"


class EstadisticasModelosDetalle(Base):
    __tablename__ = "EstadisticasModelosDetalle"

    Id = Column("Id", Integer, primary_key=True, autoincrement=True, index=True)
    EstadisticasModelosId = Column(
        "EstadisticasModelosId",
        Integer,
        ForeignKey("EstadisticasModelos.Id"),
        nullable=False,
        index=True,
    )
    TipoOperacion = Column("TipoOperacion", SQLEnum(TipoOperacionEnum, name="tipooperacionenum"), nullable=False)
    NombreModelo = Column("NombreModelo", String(255), nullable=False)
    InputTokens = Column("InputTokens", Integer, nullable=False)
    OutputTokens = Column("OutputTokens", Integer, nullable=False)
    ThoughtsTokens = Column("ThoughtsTokens", Integer, nullable=False)
    TotalTokens = Column("TotalTokens", Integer, nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

    estadistica_modelo = relationship("EstadisticasModelos", back_populates="detalles")