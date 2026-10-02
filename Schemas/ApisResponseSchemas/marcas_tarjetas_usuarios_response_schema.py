from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer
from Utils.formateo_fechas import formatear_fecha_larga

class MarcasTarjetasUsuariosResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    NombreMarca: str
    IsActive:bool
    FechaRegistro: datetime

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value)