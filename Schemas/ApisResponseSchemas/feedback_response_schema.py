from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_serializer
from Utils.formateo_fechas import formatear_fecha_larga
class ImagenesResportadasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url_imagen: list[str]
    fecha_registro: datetime
    usuario_id: int
    respuesta: Optional[Any] = None
    observacion:  Optional[str] = None
    estado_resolucion:  Optional[str] = None
    resolucion:  Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    id_usuario: int
    nombre_usuario:  Optional[str] = None
    apellido_usuario:  Optional[str] = None
    user_name:  Optional[str] = None


    @field_serializer("fecha_resolucion")
    def serialize_fecha_resolucion(self, value: Optional[datetime]) -> Optional[str]:
        return formatear_fecha_larga(value) 

    @field_serializer("fecha_registro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value) 