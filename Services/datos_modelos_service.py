from sqlalchemy.ext.asyncio import AsyncSession
from Schemas.ApisResponseSchemas.datos_modelos_response_shema import (
    EstadisticasErroresSchema, EstadisticasSchema, ResponseDatosModelosSchema
)
from Schemas.Respuestas import RespuestaFuncion
from Repositories.estadisticas_modelos_queries import obtener_datos_modelos
from Utils.resumen_datos_modelos import calcular_estadisticas
from Utils.error_utils import limpiar_mensaje_error_bd
from Integrations.google_ocr_client import disponibilidad_lector_imagen
from Integrations.groq_clasificador import disponibilidad_clasificador
async def datos_modelos(db: AsyncSession) -> RespuestaFuncion:
    try:
        respuesta_repo = await obtener_datos_modelos(db)

        if not respuesta_repo.success_registro:
            return respuesta_repo

        registros = respuesta_repo.data_registro["estadisticas"]
        registro_errores = respuesta_repo.data_registro["errores"]
        
        calculo = calcular_estadisticas(registros)
        estadisticas = EstadisticasSchema.desde_calculo(calculo, registros)
        estadisticas_errores = EstadisticasErroresSchema.desde_registros(registro_errores)
        modelos_lector_imagen = await disponibilidad_lector_imagen()
        modelos_clasificador = await disponibilidad_clasificador()
        resultado = ResponseDatosModelosSchema(
            estadisticas=estadisticas,
            estadisticas_errores=estadisticas_errores,
            disponibilidad={
                "lector_imagen": [
                    modelo["name"].rsplit("/", 1)[-1]
                    for modelo in modelos_lector_imagen
                ],
                "clasificador": [
                    modelo.id
                    for modelo in modelos_clasificador.data
                ],
            },
        )

        return RespuestaFuncion(data_registro=resultado)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))