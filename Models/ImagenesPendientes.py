from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func,Text
from sqlalchemy.orm import relationship

from Config.settings import Base


class ImagenesPendientes(Base):
    __tablename__ = "ImagenesPendientes"

    Id = Column("Id", Integer, primary_key=True, index=True)
    CodigoTarea = Column("CodigoTarea", String(255), nullable=False, index=True)
    UrlImagen = Column("UrlImagen", String(500), nullable=False, unique=True, index=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    Motivo= Column("Motivo", Text, nullable=True)
    usuario = relationship("Usuarios", back_populates="imagenes_pendientes")
    