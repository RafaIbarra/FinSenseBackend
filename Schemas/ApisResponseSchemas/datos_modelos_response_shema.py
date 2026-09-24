#./Schemas/ApisResponceShemas    
from pydantic import BaseModel, ConfigDict, Field, computed_field,field_validator
from datetime import datetime
from typing import Optional

##REGISTRO EN DETALLE
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
    # imagenes:list[ImagenSchema]
    tamanno_img: Optional[int] = Field(default=0,validation_alias="imagenes")
    gasto_registrado: Optional[bool] = Field(default=None,validation_alias="movimiento")
    usuario: Optional[str] = None
    

    
    
    @field_validator("tamanno_img", mode="before")
    @classmethod
    def obtener_tamanno(cls, value):
        
        if not value:
            return 0
    
        return value[0].TamañoImagen 

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
    
        
    
        
# DATOS ESTADISTICAS TOKENS   

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
    NumeroMes: int
    Mes:str

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

#DATOS ESTADISTICAS USUARIOS
class TokensUsuarioSchema(BaseModel):
    InputTokens: int = 0
    OutputTokens: int = 0
    ThoughtsTokens: int = 0
    TotalTokens: int = 0

    PorcentajeInputTokens: float = 0
    PorcentajeOutputTokens: float = 0
    PorcentajeThoughtsTokens: float = 0
    PorcentajeTotalTokens: float = 0

class TokensUsuarioPorOperacionSchema(TokensTotalesSchema):
    TipoOperacion: str

class TokensUsuarioPorModeloSchema(TokensTotalesSchema):
    NombreModelo: str

class GastoUsuarioSchema(BaseModel):
    gasto_registrado: bool
    cantidad_registros: int = 0
    total_tamanno_img: int = 0

class DataUsuarioItemSchema(BaseModel):
    NombreUsuario: str

    tokens: TokensUsuarioSchema

    por_tipo_operacion: list[TokensUsuarioPorOperacionSchema] = Field(
        default_factory=list
    )

    por_modelo: list[TokensUsuarioPorModeloSchema] = Field(
        default_factory=list
    )

    cantidad_registros: int = 0

    total_tamanno_img: int = 0

    por_gasto_registrado: list[GastoUsuarioSchema] = Field(
        default_factory=list
    )    

class DataUsuarioSchema(BaseModel):
    datos: list[DataUsuarioItemSchema] = Field(
        default_factory=list
    )

class EstadisticasSchema(BaseModel):
    data_tokens: DataTokensSchema
    data_usuarios: DataUsuarioSchema
    detalles_registros: list[DatosEstadisticosSchema]

class ResponseSchema(BaseModel):
    estadisticas: EstadisticasSchema

    