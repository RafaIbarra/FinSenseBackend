from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class Temas(Base):
	__tablename__ = "Temas"

	Id = Column("Id", Integer, primary_key=True, autoincrement=True, index=True)
	NombreTema = Column("NombreTema", String(200), nullable=False, unique=True, index=True)
	Tipo = Column("Tipo", String(200), nullable=False)
	Descripcion = Column("Descripcion", String(500), nullable=True)
	FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

	preferencias = relationship(
		"PreferenciasUsuario",
		back_populates="tema",
		cascade="all, delete-orphan",
	)
