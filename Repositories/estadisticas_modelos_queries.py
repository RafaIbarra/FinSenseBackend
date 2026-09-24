from sqlalchemy import  select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from Models.EstadisticasModelos import EstadisticasModelos
from Schemas.Respuestas import RespuestaFuncion
from Schemas.ApisResponseSchemas.datos_modelos_response_shema import DatosEstadisticosSchema,ResponseSchema,EstadisticasSchema
from fastapi.encoders import jsonable_encoder
from Utils.calculo_estadisticas_modelos import calcular_estadisticas
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

async def datos_modelos(db: AsyncSession):
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
        

        # datos_stats = [DatosEstadisticosSchema.model_validate(valor)for valor in valores]
        
        data_tokens = calcular_estadisticas(valores)
        # resultado=[
        #     ResponseSchema(
        #         estadisticas=EstadisticasSchema(
        #             data_tokens=data_tokens
        #             ,detalles_registros=datos_stats
        #         )
        #     )
        # ]
        
        

        return RespuestaFuncion(data_registro=data_tokens)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    