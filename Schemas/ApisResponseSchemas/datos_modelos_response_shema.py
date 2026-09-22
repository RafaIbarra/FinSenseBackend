    
from pydantic import BaseModel, ConfigDict, Field, computed_field,field_validator
from datetime import datetime
from typing import Optional


class DetalleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    TipoOperacion:Optional[str]=""
    NombreModelo:Optional[str]=""
    InputTokens:Optional[int] = 0
    OutputTokens:Optional[int] = 0
    ThoughtsTokens:Optional[int] = 0
    TotalTokens:Optional[int] = 0
    FechaRegistro:Optional[datetime] = None
    
class ImagenSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    UrlsPermanente: Optional[str] = Field(
        default=None,
        exclude=True
    )
    TamañoImagen: Optional[int]=0
    @computed_field
    @property
    def TipoRegistro(self) -> str:
        return 'Permanente' if len(self.UrlsPermanente)>0 else 'Temporal'

class DatosEstadisticosSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    FechaRegistro: datetime
    datos_modelo: list[DetalleSchema] = Field(default_factory=list,validation_alias="detalles")
    tamanno_img: Optional[int] = Field(default=0,validation_alias="imagenes")
    gasto_registrado: Optional[bool] = Field(default=None,validation_alias="movimiento")
    usuario: Optional[str] = None
    

    
    
    @field_validator("tamanno_img", mode="before")
    @classmethod
    def obtener_tamanno(cls, value):
        if value is None:
            return None
        return value[0].TamañoImagen or 0

    @field_validator("usuario", mode="before")
    @classmethod
    def obtener_username(cls, value):
        if value is None:
            return None

        return value.UserName
    
    @field_validator("gasto_registrado", mode="before")
    @classmethod
    def obtener_movimiento(cls, value):
        if value is None:
            return False
        else:
            return True
    
        
    
        
        

class TokensTotalesSchema(BaseModel):
    InputTokens: int = 0
    OutputTokens: int = 0
    ThoughtsTokens: int = 0
    TotalTokens: int = 0

class TokensPorOperacionSchema(TokensTotalesSchema):
    TipoOperacion: str

class TokensPorModeloSchema(BaseModel):
    NombreModelo: str
    Resumen: TokensTotalesSchema
    distribucion: list[TokensPorOperacionSchema] = Field(
        default_factory=list
    )

class TokensPorDiaSchema(TokensTotalesSchema):
    Dia: int

class TokensPorMesSchema(BaseModel):
    Mes: int
    datos: list[TokensPorDiaSchema] = []

class TokensPorAñoSchema(BaseModel):
    Año: int
    datos: list[TokensPorMesSchema] = []

class DataTokensSchema(BaseModel):
    total_general: TokensTotalesSchema
    por_tipo_operacion: list[TokensPorOperacionSchema] = Field(
        default_factory=list
    )
    por_modelo: list[TokensPorModeloSchema] = Field(
        default_factory=list
    )
    por_fecha: list[TokensPorAñoSchema] = Field(
        default_factory=list
    )


class EstadisticasSchema(BaseModel):
    data_tokens: DataTokensSchema
    detalles_registros: list[DatosEstadisticosSchema]

class ResponseSchema(BaseModel):
    estadisticas: EstadisticasSchema

    