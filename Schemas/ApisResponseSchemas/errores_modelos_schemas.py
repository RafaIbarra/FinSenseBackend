from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer,computed_field
from Utils.formateo_fechas import formatear_fecha_larga
from Utils.clasificador_error_modelos import clasificar_error
class ErroresModelosResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    Proceso: str
    Rubro: Optional[str] = None
    NombreModelo: str
    RespuestaError: Optional[str] = None
    FechaRegistro: datetime

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value)

    @computed_field
    @property
    def TipoError(self) -> str:
        return clasificar_error(self.RespuestaError)