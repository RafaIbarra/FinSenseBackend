import enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, String, Text, func

from Config.settings import Base


class TipoErrorEnum(enum.Enum):
    Modelo = "Modelo"
    EstructuraDatos = "EstructuraDatos"
    RegistroDato = "RegistroDato"


class ErroresProcesamientoImagenesPendientes(Base):
    __tablename__ = "ErroresProcesamientoImagenesPendientes"

    IdRegistro = Column("IdRegistro", Integer, primary_key=True, autoincrement=True, index=True)
    CodigoTarea = Column("CodigoTarea", String(255), nullable=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    TipoError = Column("TipoError", SQLEnum(TipoErrorEnum, name="tipoerrorenum"), nullable=False)
    Error = Column("Error", Text, nullable=False)

