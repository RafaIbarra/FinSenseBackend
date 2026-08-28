from datetime import datetime
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from Models.UrlsImagenesTemporales import UrlsImagenesTemporales
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd
from Integrations.r2_storage import *


async def registrar_urls_temporales(db: AsyncSession, id_usuario: int, list_urls: List[str]):
    try:
        if not id_usuario:
            return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

        if not list_urls:
            return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una URL")

        ts = datetime.now()
        formateado=ts.strftime("%Y_%m_%d_T_%H_%M_%S")
        codigo_proceso = f'U_{id_usuario}_F_{formateado}'

        db.add_all([
            UrlsImagenesTemporales(
                CodigoProceso=codigo_proceso,
                UrlImagen=url,
                UsuarioId=id_usuario,
                FechaProcesado=None,
                PendienteEliminacion=True,
                FechaEliminacion=None,
            )
            for url in list_urls
        ])
        await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        
        for ur in list_urls:
            try:
                r2_storage.delete_temp_image(ur)
            except Exception:
                pass
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    
async def procesar_urls_temporales(db: AsyncSession, id_usuario: int, list_urls: List[str]):
    try:
        if not id_usuario:
            return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

        if not list_urls:
            return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una URL")

        fecha_procesado = datetime.now()
        await db.execute(
            update(UrlsImagenesTemporales)
            .where(
                UrlsImagenesTemporales.UsuarioId == id_usuario,
                UrlsImagenesTemporales.UrlImagen.in_(list_urls),
            )
            .values(
                FechaProcesado=fecha_procesado,
                FechaEliminacion=fecha_procesado,
                PendienteEliminacion=False,
            )
        )
        await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
                  
