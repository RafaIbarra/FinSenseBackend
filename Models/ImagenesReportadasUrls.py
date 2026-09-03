from sqlalchemy import Column, ForeignKey, Integer, String,func,DateTime
from sqlalchemy.orm import relationship

from Config.settings import Base


class ImagenesReportadasUrls(Base):
    __tablename__ = "ImagenesReportadasUrls"

    Id = Column("Id", Integer, primary_key=True, autoincrement=True, index=True)
    ImagenesReportadasId = Column(
        "ImagenesReportadasId",
        Integer,
        ForeignKey("ImagenesReportadas.Id"),
        nullable=False,
        index=True,
    )

    UrlImagen = Column("UrlImagen", String(500), nullable=False, unique=True, index=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    imagen_reporte = relationship("ImagenesReportadas", back_populates="urls")
