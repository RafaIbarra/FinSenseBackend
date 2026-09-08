from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class PreferenciasUsuario(Base):
	__tablename__ = "PreferenciasUsuario"

	Id = Column("Id", Integer, primary_key=True, autoincrement=True, index=True)
	UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
	TemaId = Column("TemaId", Integer, ForeignKey("Temas.Id"), nullable=False, index=True)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

	usuario = relationship("Usuarios", back_populates="preferencias")
	tema = relationship("Temas", back_populates="preferencias")
