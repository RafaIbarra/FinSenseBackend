from pydantic import BaseModel, Field
from typing import List, Optional

from Models.EstadisticasModelos import OrigenEstadisticaEnum,EstadoEstadisticaEnum
from Models.EstadisticasModelosDetalle import TipoOperacionEnum


class RegistroEstadisticaDetalle(BaseModel):
    tipo_operacion: TipoOperacionEnum
    nombre_modelo: str
    input_tokens: int
    output_tokens: int
    thoughts_tokens: int
    total_tokens: int


class RegistroEstadisticaImagen(BaseModel):
    url_temporal: str
    urls_permanente: str
    tamano_imagen: int=0


class RegistroEstadisticas(BaseModel):
    id: int = 0
    usuario_id: int = 0
    origen: OrigenEstadisticaEnum
    detalles: List[RegistroEstadisticaDetalle] = Field(default_factory=list)
    imagenes: List[RegistroEstadisticaImagen] = Field(default_factory=list)

class ActualizarEstadisticas(BaseModel):
    id:int =0
    estado: EstadoEstadisticaEnum
    imagenes: List[RegistroEstadisticaImagen] = Field(default_factory=list)
    id_movimiento: Optional[int] = None
