from sqlalchemy import Column, Integer, String, DateTime, Boolean,ForeignKey, func
from sqlalchemy.orm import relationship


from Config.settings import Base


class MarcasTarjetas(Base):
    __tablename__ = "MarcasTarjetas"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreMarca = Column("NombreMarca", String(200), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    IsActive = Column("IsActive", Boolean, nullable=False, default=True, server_default="true")
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)

    usuario = relationship("Usuarios", back_populates="marcas_tarjetas")
    medios_pagos_usuarios = relationship(
        "MediosPagosUsuarios",
        back_populates="marca_tarjeta",
    )