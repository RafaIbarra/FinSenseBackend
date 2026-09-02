from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class Usuarios(Base):
    __tablename__ = "Usuarios"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreUsuario = Column("NombreUsuario", String(100), nullable=False)
    ApellidoUsuario = Column("ApellidoUsuario", String(100), nullable=False)
    UserName = Column("UserName", String(50), nullable=False, unique=True, index=True)
    Correo = Column("Correo", String(255), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    Password = Column("Password", String(255), nullable=False)

    sesiones_activas = relationship(
        "SesionesActivas",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    movimientos_gastos = relationship(
        "MovimientosGastos",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    imagenes_pendientes = relationship(
        "ImagenesPendientes",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    imagenes_reportadas = relationship(
        "ImagenesReportadas",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    urls_imagenes_temporales = relationship("UrlsImagenesTemporales",back_populates="usuario",
            cascade="all, delete-orphan",)

    envios_correos = relationship(
        "EnvioCorreos",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )