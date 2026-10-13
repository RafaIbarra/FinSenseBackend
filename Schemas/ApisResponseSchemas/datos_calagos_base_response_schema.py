from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer
from Utils.formateo_fechas import formatear_fecha_larga
class EmpresasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    NombreEmpresa: str
    Rubro: Optional[str] = None
    Ruc: str
    UrlLogo: Optional[str] = None
    FechaRegistro: datetime
    CantidadRegistros: int=0

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value) 

class TipoMediosResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    NombreTipo: str
    EsDebito: Optional[bool] = None
    FechaRegistro: datetime
    SolicitarMarca: Optional[bool] = None
    SolicitarEntidad: Optional[bool] = None
    

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value) 
    
class CanalesPagosResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    NombreCanal: str
    FechaRegistro: datetime
    

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value) 

class CatalogosBaseResponse(BaseModel):
    Empresas: list[EmpresasResponse]
    TiposMedios: list[TipoMediosResponse]
    Canales: list[CanalesPagosResponse]