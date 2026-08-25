from pydantic import BaseModel
from typing import Any, Optional,List



class RespuestaImagenesSubidas(BaseModel):
    urls_img: List[str] = []   # Conceptos/descripciones de los artículos
    success: Optional[bool] = True
    mensaje_error:str=""

