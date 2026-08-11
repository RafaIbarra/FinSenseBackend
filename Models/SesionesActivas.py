from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from Config.Settings import Base


class SesionesActivas(Base):
    __tablename__ = "SesionesActivas"

    Id = Column("Id", Integer, primary_key=True, index=True)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    Dispositivo = Column("Dispositivo", String(255), nullable=False)
    IpConexion = Column("IpConexion", String(45), nullable=False)
    FechaConexion = Column("FechaConexion", DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuarios", back_populates="sesiones_activas")
