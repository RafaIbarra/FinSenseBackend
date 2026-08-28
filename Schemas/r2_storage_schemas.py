# Schemas/r2_storage_schemas.py
from pydantic import BaseModel
from typing import Any, Optional, List
import enum


class TipoUrlEnum(enum.Enum):
    Temporal = "Temporal"
    Procesada = "Procesada"


class RespuestaImagenesSubidas(BaseModel):
    urls_img: List[str] = []
    success: Optional[bool] = True
    mensaje_error: str = ""
    tipo_url: Optional[TipoUrlEnum] = None