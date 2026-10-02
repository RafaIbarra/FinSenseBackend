from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship


from Config.settings import Base


class TiposMediosPagos(Base):
    __tablename__ = "TiposMediosPagos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    NombreTipo = Column("NombreTipo", String(200), nullable=False)
    EsDebito = Column("EsDebito", Boolean,default=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    SolicitarMarca=Column("SolicitarMarca", Boolean, nullable=False, default=True, server_default="true")
    SolicitarEntidad=Column("SolicitarEntidad", Boolean, nullable=False, default=True, server_default="true")
    medios_pagos_usuarios = relationship(
        "MediosPagosUsuarios",
        back_populates="tipo_medio_pago",
    )