from pydantic import BaseModel,StrictInt,Field,ValidationError
from .integrations_schemas import FacturaExtraida,ClasificacionGasto
from .r2_storage_schemas import RespuestaImagenesSubidas
from Models.MovimientosGastos import TipoRegistroEnum
from typing import Optional
import json
class RegistroMovimientoGastoRequest(BaseModel):
    id:int=0
    factura: FacturaExtraida
    clasificacion: Optional[ClasificacionGasto] = None
    imagenes: Optional[RespuestaImagenesSubidas] =None
    tipo_registro: TipoRegistroEnum
    id_stas : int =0  
    medio_pago:list=[]

class MedioPagoIn(BaseModel):
    id_medio: StrictInt
    monto_medio: float = Field(..., gt=0)
    canal_pago_id: Optional[StrictInt] = None

    model_config = {"extra": "forbid"}  # rechaza keys desconocidas


def parsear_medios_pago(texto: str) -> list[dict]:
    try:
        data = json.loads(texto)
    except json.JSONDecodeError:
        raise ValueError("medio_pago no es un JSON válido.")

    if not isinstance(data, list):
        raise ValueError("medio_pago debe ser una lista de objetos.")

    try:
        medios = [MedioPagoIn(**item) for item in data]
    except TypeError:
        raise ValueError("Cada elemento de medio_pago debe ser un objeto.")
    except ValidationError as e:
        errores = "; ".join(
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()
        )
        raise ValueError(f"medio_pago inválido: {errores}")

    # exclude_none evita guardar "canal_pago_id": null cuando no viene
    return [m.model_dump(exclude_none=True) for m in medios]