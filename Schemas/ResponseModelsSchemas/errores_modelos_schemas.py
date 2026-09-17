from Schemas.sqlalchemy_schemas import crear_schema_lista_desde_modelo
from Models.ErroresModelos import ErroresModelos
from Utils.clasificador_error_modelos import error_a_dict
ErrorModeloResponse = crear_schema_lista_desde_modelo(
    ErroresModelos,
    campos_extra={"TipoError": (str, ...)},
    transformador=error_a_dict,
)