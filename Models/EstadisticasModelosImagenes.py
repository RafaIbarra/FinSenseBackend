from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from Config.settings import Base


class EstadisticasModelosImagenes(Base):
    __tablename__ = "EstadisticasModelosImagenes"

    Id = Column("Id", Integer, primary_key=True, autoincrement=True, index=True)
    EstadisticasModelosId = Column(
        "EstadisticasModelosId",
        Integer,
        ForeignKey("EstadisticasModelos.Id"),
        nullable=False,
        index=True,
    )
    UrlTemporal = Column("UrlTemporal", String(500), nullable=False)
    UrlsPermanente = Column("UrlsPermanente", String(500), nullable=False)
    TamañoImagen = Column("TamañoImagen", Integer, nullable=False)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)

    estadistica_modelo = relationship("EstadisticasModelos", back_populates="imagenes")