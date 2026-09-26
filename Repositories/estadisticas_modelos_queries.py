#.Repositories/ 
from sqlalchemy import  select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from Models.EstadisticasModelos import EstadisticasModelos
from Schemas.Respuestas import RespuestaFuncion

from Utils.error_utils import limpiar_mensaje_error_bd
async def datos_estadisticas_modelos(db: AsyncSession):
    try:
        result = await db.execute(
                    select(EstadisticasModelos)
                    .options(
                        selectinload(EstadisticasModelos.detalles),
                        selectinload(EstadisticasModelos.imagenes),
                        selectinload(EstadisticasModelos.movimiento),
                    )
                    .order_by(EstadisticasModelos.FechaRegistro.desc())
                )
        valores = result.scalars().all()
        
        return RespuestaFuncion(data_registro=valores)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))

async def obtener_datos_modelos(db: AsyncSession):
    try:
        result = await db.execute(
                    select(EstadisticasModelos)
                    .options(
                        selectinload(EstadisticasModelos.detalles),
                        selectinload(EstadisticasModelos.imagenes),
                        selectinload(EstadisticasModelos.movimiento),
                        selectinload(EstadisticasModelos.usuario),
                    )
                    .order_by(EstadisticasModelos.FechaRegistro.desc())
                )
        valores = result.scalars().all()
                
        return RespuestaFuncion(data_registro=valores)
        
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    