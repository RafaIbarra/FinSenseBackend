# Services/tareas_pendientes_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from Utils.datos_tareas_pendientes import resumen_datos_tareas

from Repositories.tasks_queries import obtener_datos_tareas
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd




async def datos_tareas(db: AsyncSession) -> RespuestaFuncion:
    try:
        respuesta_repo = await obtener_datos_tareas(db)

        if not respuesta_repo.success_registro:
            return respuesta_repo

        registros = respuesta_repo.data_registro

        
        resumen = resumen_datos_tareas(registros)

        return RespuestaFuncion(data_registro=resumen)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))