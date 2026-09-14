import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class TipoErrorEnum(enum.Enum):
    Modelo = "Modelo"
    EstructuraDatos = "EstructuraDatos"
    RegistroDato = "RegistroDato"


class ErroresProcesamientoImagenesPendientes(Base):
    __tablename__ = "ErroresProcesamientoImagenesPendientes"

    IdRegistro = Column("IdRegistro", Integer, primary_key=True, autoincrement=True, index=True)
    ImagenesPendientesId = Column(
        "ImagenesPendientesId",
        Integer,
        ForeignKey("ImagenesPendientes.Id"),
        nullable=False,
        index=True,
    )
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    TipoError = Column("TipoError", SQLEnum(TipoErrorEnum, name="tipoerrorenum"), nullable=False)
    Error = Column("Error", Text, nullable=False)

    imagen_pendiente = relationship("ImagenesPendientes", back_populates="errores_procesamiento")