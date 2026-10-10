from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from Schemas.ApisResponseSchemas.empresas_response_schema import EmpresasUsuarioResponse


class MedioPagoCargaGastosResponse(BaseModel):
    Id: int
    UsuarioId: int
    TipoMedioPagoId: int
    EntidadUsuarioId: Optional[int] = None
    MarcaTarjetaId: Optional[int] = None
    FechaRegistro: datetime
    IsActive: bool
    tipo_medio_pago: Optional[str] = None
    entidad_usuario: Optional[str] = None
    marca_tarjeta: Optional[str] = None


class CanalPagoCargaGastosResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    NombreCanal: str
    FechaRegistro: datetime


class ReferencialesCargaGastos(BaseModel):
    Empresas: list[EmpresasUsuarioResponse]
    MediosPagos: list[MedioPagoCargaGastosResponse]
    Canales: list[CanalPagoCargaGastosResponse]