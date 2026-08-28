from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, Boolean
from sqlalchemy.orm import relationship

from Config.settings import Base


class UrlsImagenesTemporales(Base):
    __tablename__ = "UrlsImagenesTemporales"

    Id = Column("Id", Integer, primary_key=True, index=True)
    CodigoProceso = Column("CodigoProceso", String(255), nullable=False, index=True)
    UrlImagen = Column("UrlImagen", String(500), nullable=False, unique=True, index=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    FechaProcesado = Column("FechaProcesado", DateTime(timezone=True), nullable=True)
    PendienteEliminacion = Column("PendienteEliminacion", Boolean, default=True, nullable=False)
    FechaEliminacion = Column("FechaEliminacion", DateTime(timezone=True), nullable=True)
    
    

    usuario = relationship("Usuarios", back_populates="urls_imagenes_temporales")
    