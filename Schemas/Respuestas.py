from pydantic import BaseModel
from typing import Any, Optional,List
from Schemas.integrations_schemas import FacturaExtraida,ClasificacionGasto
from Models.MovimientosGastos import TipoRegistroEnum
from Schemas.r2_storage_schemas import RespuestaImagenesSubidas
class RespuestaFuncion(BaseModel):
    success_registro: Optional[bool] = True
    mensaje: Optional[str] = None
    data_registro: Optional[Any] = None




    

class RespuestaProcesamientoImgFacturas(BaseModel):
    procesamiento_correcto:Optional[bool] = True
    factura:Optional[FacturaExtraida] = None
    clasificacion:Optional[ClasificacionGasto]=None
    imagenes:Optional[RespuestaImagenesSubidas]=None
    solicita_envio_pendiente:Optional[bool] = True
    tipo_registro: Optional[TipoRegistroEnum] = None
    mensaje_error:str=""
    