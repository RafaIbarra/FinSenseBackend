from datetime import datetime
from typing import Any, Callable, Optional, Type

from pydantic import BaseModel, ConfigDict, RootModel, create_model, field_serializer, model_validator

from Utils.formateo_fechas import formatear_fecha_larga


class ModeloSQLAlchemyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", check_fields=False)
    def serialize_values(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return formatear_fecha_larga(value)
        return value


def crear_schema_desde_modelo(
    modelo: Type[Any],
    *,
    nombre: Optional[str] = None,
    campos_extra: Optional[dict[str, Any]] = None,
) -> Type[BaseModel]:
    campos: dict[str, tuple[Any, Any]] = {}

    for columna in modelo.__table__.columns:
        try:
            tipo = columna.type.python_type
        except (AttributeError, NotImplementedError):
            tipo = Any

        if columna.nullable:
            campos[columna.name] = (Optional[tipo], None)
        else:
            campos[columna.name] = (tipo, ...)

    if campos_extra:
        campos.update(campos_extra)

    return create_model(
        nombre or f"{modelo.__name__}Response",
        __base__=ModeloSQLAlchemyResponse,
        **campos,
    )


def crear_schema_lista_desde_modelo(
    modelo: Type[Any],
    *,
    nombre: Optional[str] = None,
    campos_extra: Optional[dict[str, Any]] = None,
    transformador: Optional[Callable[[Any], Any]] = None,
) -> Type[RootModel]:
    schema_fila = crear_schema_desde_modelo(
        modelo,
        nombre=f"{modelo.__name__}ItemResponse",
        campos_extra=campos_extra,
    )

    if transformador is None:
        return create_model(
            nombre or f"{modelo.__name__}Response",
            __base__=RootModel[list[schema_fila]],
        )

    class ListaResponse(RootModel[list[schema_fila]]):
        @model_validator(mode="before")
        @classmethod
        def transformar(cls, value: Any) -> Any:
            if isinstance(value, (list, tuple)):
                return [transformador(item) for item in value]
            return value

    ListaResponse.__name__ = nombre or f"{modelo.__name__}Response"
    ListaResponse.__qualname__ = ListaResponse.__name__
    return ListaResponse
