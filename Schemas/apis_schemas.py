from pydantic import BaseModel
from .integrations_schemas import FacturaExtraida,ClasificacionGasto
from .r2_storage_schemas import RespuestaImagenesSubidas
from Models.MovimientosGastos import TipoRegistroEnum
class RegistroMovimientoGastoRequest(BaseModel):
    factura: FacturaExtraida
    clasificacion: ClasificacionGasto
    imagenes: RespuestaImagenesSubidas
    tipo_registro: TipoRegistroEnum  