from pydantic import BaseModel,ConfigDict
from typing import List, Optional

class FacturaExtraida(BaseModel):
    model_config = ConfigDict(extra='forbid')

    empresa: Optional[str] = None
    rubro: Optional[str] = None
    ruc_empresa: Optional[str] = None
    fecha: Optional[str] = None
    numero_factura: Optional[str] = None
    total: Optional[float] = None
    iva_diez: Optional[float] = None
    iva_cinco: Optional[float] = None
    fiabilidad: str = "Malo"  # Excelente, Bueno, Malo
    detalle: List[str] = []   # Conceptos/descripciones de los artículos
    Model: Optional[str] = None
    success_registro: Optional[bool] = True
    mensaje_error:str=""
    data_correct: Optional[bool] = True

class ClasificacionGasto(BaseModel):
    categoria: str
    etiquetas: List[str]
    modelo_clasificador: str


