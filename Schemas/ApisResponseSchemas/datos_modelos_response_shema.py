#./Schemas/ApisResponceShemas    
from pydantic import BaseModel, ConfigDict, Field, computed_field,field_validator
from datetime import datetime
from typing import Optional
from Schemas.ApisResponseSchemas.errores_modelos_schemas import ErroresModelosResponse

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
        return 'Permanente' if self.UrlsPermanente else 'Temporal'

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
        return value is not None


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
    distribucion: list[TokensPorOperacionSchema] = Field(default_factory=list)

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
    por_tipo_operacion: list[TokensPorOperacionSchema] = Field(default_factory=list)
    por_modelo: list[TokensPorModeloSchema] = Field(default_factory=list)
    por_fecha: list[TokensPorAñoSchema] = Field(default_factory=list)


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
    por_tipo_operacion: list[TokensUsuarioPorOperacionSchema] = Field(default_factory=list)
    por_modelo: list[TokensUsuarioPorModeloSchema] = Field(default_factory=list)
    cantidad_registros: int = 0
    total_tamanno_img: int = 0
    por_gasto_registrado: list[GastoUsuarioSchema] = Field(default_factory=list)    

class DataUsuarioSchema(BaseModel):
    datos: list[DataUsuarioItemSchema] = Field(default_factory=list)


class EstadisticasSchema(BaseModel):
    data_tokens: DataTokensSchema
    data_usuarios: DataUsuarioSchema
    detalles_registros: list[DatosEstadisticosSchema]

    @classmethod
    def desde_calculo(cls, calculo: dict, valores) -> "EstadisticasSchema":
        """
        calculo: dict crudo devuelto por Utils.calculo_estadisticas_modelos.calcular_estadisticas
                 (shape: {"data_tokens": {...}, "data_usuarios": {...}})
        valores: registros ORM originales (EstadisticasModelos), usados para
                 construir detalles_registros vía model_validate.
        """
        return cls(
            data_tokens=DataTokensSchema(**calculo["data_tokens"]),
            data_usuarios=DataUsuarioSchema(**calculo["data_usuarios"]),
            detalles_registros=[
                DatosEstadisticosSchema.model_validate(registro)
                for registro in valores
            ],
        )


class ErrorPorTipoSchema(BaseModel):
    TipoError: str
    cantidad: int
    porcentaje: float


class ErrorPorProcesoSchema(BaseModel):
    Proceso: str
    cantidad: int
    porcentaje: float


class ErrorPorModeloSchema(BaseModel):
    NombreModelo: str
    Proceso: str
    cantidad: int
    porcentaje: float


class EstadisticasErroresSchema(BaseModel):
    total_general: int = 0
    por_tipo_error: list[ErrorPorTipoSchema] = Field(default_factory=list)
    por_proceso: list[ErrorPorProcesoSchema] = Field(default_factory=list)
    por_modelo: list[ErrorPorModeloSchema] = Field(default_factory=list)
    detalles_registros: list[ErroresModelosResponse] = Field(default_factory=list)

    @classmethod
    def desde_registros(cls, registros) -> "EstadisticasErroresSchema":
        detalles = [
            ErroresModelosResponse.model_validate(registro)
            for registro in registros
        ]
        total_general = len(detalles)
        por_tipo_error = {}
        por_proceso = {}
        por_modelo = {}

        for detalle in detalles:
            por_tipo_error[detalle.TipoError] = por_tipo_error.get(detalle.TipoError, 0) + 1
            por_proceso[detalle.Proceso] = por_proceso.get(detalle.Proceso, 0) + 1
            clave_modelo = (detalle.NombreModelo, detalle.Proceso)
            por_modelo[clave_modelo] = por_modelo.get(clave_modelo, 0) + 1

        def calcular_porcentaje(cantidad: int) -> float:
            if not total_general:
                return 0
            return round(cantidad / total_general * 100, 2)

        return cls(
            total_general=total_general,
            por_tipo_error=[
                ErrorPorTipoSchema(
                    TipoError=tipo_error,
                    cantidad=cantidad,
                    porcentaje=calcular_porcentaje(cantidad),
                )
                for tipo_error, cantidad in sorted(por_tipo_error.items())
            ],
            por_proceso=[
                ErrorPorProcesoSchema(
                    Proceso=proceso,
                    cantidad=cantidad,
                    porcentaje=calcular_porcentaje(cantidad),
                )
                for proceso, cantidad in sorted(por_proceso.items())
            ],
            por_modelo=[
                ErrorPorModeloSchema(
                    NombreModelo=nombre_modelo,
                    Proceso=proceso,
                    cantidad=cantidad,
                    porcentaje=calcular_porcentaje(cantidad),
                )
                for (nombre_modelo, proceso), cantidad in sorted(por_modelo.items())
            ],
            detalles_registros=detalles,
        )


class DisponibilidadModelosSchema(BaseModel):
    lector_imagen: list[str] = Field(default_factory=list)
    clasificador: list[str] = Field(default_factory=list)


class ResponseDatosModelosSchema(BaseModel):
    estadisticas: EstadisticasSchema
    estadisticas_errores: EstadisticasErroresSchema
    disponibilidad: DisponibilidadModelosSchema
