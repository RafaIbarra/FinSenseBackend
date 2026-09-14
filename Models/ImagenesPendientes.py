from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, Boolean,text
from sqlalchemy.orm import relationship

from Config.settings import Base


class ImagenesPendientes(Base):
    __tablename__ = "ImagenesPendientes"

    Id = Column("Id", Integer, primary_key=True, index=True)
    CodigoTarea = Column("CodigoTarea", String(255), nullable=False, index=True)
    UrlImagen = Column("UrlImagen", String(500), nullable=False, unique=True, index=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    Motivo = Column("Motivo", Text, nullable=True)
    Procesado = Column("Procesado", Boolean, default=False)
    FechaProcesado = Column("FechaProcesado", DateTime(timezone=True), nullable=True)
    
    
    MovimientoId = Column(
        "MovimientoId",
        Integer,
        ForeignKey("MovimientosGastos.Id"),
        nullable=True,
        index=True
    )

    TamañoImagen = Column(
        "TamañoImagen",
        Integer,
        nullable=True,
        default=0,
        server_default=text("0")
    )

    usuario = relationship("Usuarios", back_populates="imagenes_pendientes")
    movimiento = relationship("MovimientosGastos", back_populates="imagenes_pendientes")
    errores_procesamiento = relationship(
        "ErroresProcesamientoImagenesPendientes",
        back_populates="imagen_pendiente",
        cascade="all, delete-orphan",
    )