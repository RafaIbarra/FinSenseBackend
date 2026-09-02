from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class EnvioCorreos(Base):
    __tablename__ = "EnvioCorreos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    Destinatario = Column("Destinatario", String(255), nullable=False)
    Asunto = Column("Asunto", String(255), nullable=False)
    NombreTemplate = Column("NombreTemplate", String(255), nullable=False)
    Data = Column("Data", JSON, nullable=True)
    ContextKey = Column("ContextKey", String(255), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    FechaProcesado = Column("FechaProcesado", DateTime(timezone=True), nullable=True)
    Procesado = Column("Procesado", Boolean, default=False, nullable=False)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=True, index=True)

    usuario = relationship("Usuarios", back_populates="envios_correos")
