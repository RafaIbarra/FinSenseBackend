from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func,Text
from sqlalchemy.orm import relationship

from Config.settings import Base


class ErroresModelos(Base):
    __tablename__ = "ErroresModelos"

    Id = Column("Id", Integer, primary_key=True, index=True)
    Proceso= Column("Proceso", String(255), nullable=False, index=True)
    NombreModelo= Column("NombreModelo", String(255), nullable=False, index=True)
    RespuestaError= Column("RespuestaError", Text, nullable=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    