from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer, computed_field, model_validator
from Utils.formateo_fechas import formatear_fecha_larga


class ValoresImgResponse(BaseModel):
    TotalBytes: int
    TotalMb:float
    Cantidad: int


class EstadisticasModelosDetalleResponse(BaseModel):
    TipoOperacion: Optional[str] = None
    NombreModelo: Optional[str] = None
    InputTokens: Optional[int] = None
    OutputTokens: Optional[int] = None
    ThoughtsTokens: Optional[int] = None
    TotalTokens: Optional[int] = None


class EstadisticasModelosResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    FechaRegistro: datetime
    Origen: str
    Estado: str
    IdMovimiento: Optional[int] = None
    FechaRegistroGasto: Optional[str] = None  # <- campo normal, no computed_field
    detalles: list[EstadisticasModelosDetalleResponse] = []
    ValoresImg: ValoresImgResponse = ValoresImgResponse(TotalBytes=0,TotalMb=0, Cantidad=0)

    @model_validator(mode="before")
    @classmethod
    def _calculo(cls, obj):
        imagenes = getattr(obj, "imagenes", None) or []
        total_bytes = sum(img.TamañoImagen or 0 for img in imagenes)

        obj.ValoresImg = {
            "TotalBytes": total_bytes,
            "TotalMb": round(total_bytes / (1024 * 1024), 2),
            "Cantidad": len(imagenes),
        }
        return obj

    @model_validator(mode="before")
    @classmethod
    def _fecha_procesada(cls, obj):
        movimiento = getattr(obj, "movimiento", None)
        if movimiento is not None:
            # Le agregamos el atributo directamente al objeto ORM en memoria
            obj.FechaRegistroGasto = formatear_fecha_larga(movimiento.FechaRegistro)
        else:
            obj.FechaRegistroGasto = None
        return obj



    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value)

    @computed_field
    @property
    def TotalInputTokens(self) -> int:
        return sum(d.InputTokens or 0 for d in self.detalles)

    @computed_field
    @property
    def TotalOutputTokens(self) -> int:
        return sum(d.OutputTokens or 0 for d in self.detalles)

    @computed_field
    @property
    def TotalThoughtsTokens(self) -> int:
        return sum(d.ThoughtsTokens or 0 for d in self.detalles)

    @computed_field
    @property
    def TotalTokensGeneral(self) -> int:
        return sum(d.TotalTokens or 0 for d in self.detalles)