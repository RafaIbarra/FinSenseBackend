from pydantic import BaseModel
from .integrations_schemas import FacturaExtraida,ClasificacionGasto
from .r2_storage_schemas import RespuestaImagenesSubidas
from Models.MovimientosGastos import TipoRegistroEnum
from typing import Optional

class RegistroMovimientoGastoRequest(BaseModel):
    id:int=0
    factura: FacturaExtraida
    clasificacion: Optional[ClasificacionGasto] = None
    imagenes: Optional[RespuestaImagenesSubidas] =None
    tipo_registro: TipoRegistroEnum
    id_stas : int =0  

