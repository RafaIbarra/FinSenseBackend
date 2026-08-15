from pydantic import BaseModel
from typing import Any, Optional
class RespuestaFuncion(BaseModel):
    success_registro: Optional[bool] = True
    mensaje: Optional[str] = None
    data_registro: Optional[Any] = None