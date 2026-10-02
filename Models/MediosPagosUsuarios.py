from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship


from Config.settings import Base


class MediosPagosUsuarios(Base):
    __tablename__ = "MediosPagosUsuarios"

    Id = Column("Id", Integer, primary_key=True, index=True)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    TipoMedioPagoId = Column("TipoMedioPagoId", Integer, ForeignKey("TiposMediosPagos.Id"), nullable=False, index=True)
    EntidadUsuarioId = Column("EntidadUsuarioId", Integer, ForeignKey("EntidadesUsuarios.Id"), nullable=True, index=True)
    MarcaTarjetaId = Column("MarcaTarjetaId", Integer, ForeignKey("MarcasTarjetas.Id"), nullable=True, index=True)

    usuario = relationship("Usuarios", back_populates="medios_pagos_usuarios")
    tipo_medio_pago = relationship("TiposMediosPagos", back_populates="medios_pagos_usuarios")
    entidad_usuario = relationship("EntidadesUsuarios", back_populates="medios_pagos_usuarios")
    marca_tarjeta = relationship("MarcasTarjetas", back_populates="medios_pagos_usuarios")
    movimientos_gastos_medios_pagos = relationship(
        "MovimientosGastosMediosPagos",
        back_populates="medio_pago_usuario",
    )