from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func,Boolean
from sqlalchemy.orm import relationship

from Config.settings import Base


class SesionesActivas(Base):
    __tablename__ = "SesionesActivas"

    Id = Column("Id", Integer, primary_key=True, index=True)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    
    # ─── NUEVOS CAMPOS ─────────────────────────────────────────────────────────
    SessionId = Column("SessionId", String(36), unique=True, nullable=False, index=True)
    # UUID v4 de la sesión. Se guarda en el JWT para validar que siga activa.
    
    EsMovil = Column("EsMovil", Boolean, default=False, nullable=False)
    # True = móvil (sesión larga), False = navegador/otro (1 hora)
    
    Activa = Column("Activa", Boolean, default=True, nullable=False)
    # Se pone en False cuando el usuario hace logout o inicia sesión en otro lado.
    # ---------------------------------------------------------------------------

    Dispositivo = Column("Dispositivo", String(255), nullable=False)
    IpConexion = Column("IpConexion", String(45), nullable=False)
    FechaConexion = Column("FechaConexion", DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuarios", back_populates="sesiones_activas")