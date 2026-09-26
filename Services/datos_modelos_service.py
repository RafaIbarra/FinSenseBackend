from sqlalchemy.ext.asyncio import AsyncSession
from Schemas.ApisResponseSchemas.datos_modelos_response_shema import (
    EstadisticasSchema, ResponseDatosModelosSchema
)
from Schemas.Respuestas import RespuestaFuncion
from Repositories.estadisticas_modelos_queries import obtener_datos_modelos
from Utils.resumen_datos_modelos import calcular_estadisticas
from Utils.error_utils import limpiar_mensaje_error_bd
async def datos_modelos(db: AsyncSession) -> RespuestaFuncion:
    try:
        respuesta_repo = await obtener_datos_modelos(db)

        if not respuesta_repo.success_registro:
            return respuesta_repo

        registros = respuesta_repo.data_registro["estadisticas"]
        
        calculo = calcular_estadisticas(registros)
        estadisticas = EstadisticasSchema.desde_calculo(calculo, registros)
        resultado = ResponseDatosModelosSchema(estadisticas=estadisticas)

        return RespuestaFuncion(data_registro=resultado)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))