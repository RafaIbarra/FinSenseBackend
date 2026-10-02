from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship


from Config.settings import Base


class EntidadesUsuarios(Base):
    __tablename__ = "EntidadesUsuarios"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreEntidad = Column("NombreEntidad", String(200), nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

    medios_pagos_usuarios = relationship(
        "MediosPagosUsuarios",
        back_populates="entidad_usuario",
    )
