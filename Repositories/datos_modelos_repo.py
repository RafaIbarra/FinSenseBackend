import re
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from Config.settings import AsyncSessionLocal
from Models.ErroresModelos import ErroresModelos
from Models.EstadisticasModelos import EstadisticasModelos,EstadoEstadisticaEnum
from Models.EstadisticasModelosDetalle import EstadisticasModelosDetalle
from Models.EstadisticasModelosImagenes import EstadisticasModelosImagenes
from Schemas.Respuestas import RespuestaFuncion
from Schemas.repos_schemas import RegistroEstadisticas,ActualizarEstadisticas

async def registro_error(error_data: dict):
    async with AsyncSessionLocal() as db:
        try:
            nuevo_error = ErroresModelos(
                Proceso=error_data.get("proceso", ""),
                NombreModelo=error_data.get("modelo", ""),
                RespuestaError=error_data.get("respuesta", ""),
            )

            db.add(nuevo_error)
            await db.commit()
            await db.refresh(nuevo_error)

            return RespuestaFuncion()

        except Exception as error:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=str(error),
            )

async def registro_stast(valores_reg: RegistroEstadisticas):
    # inicio = time.perf_counter()
    async with AsyncSessionLocal() as db:
        try:
            nuevo_stats = EstadisticasModelos(
                UsuarioId=valores_reg.usuario_id,
                Origen=valores_reg.origen,
                Estado=EstadoEstadisticaEnum.Pendiente,
                IdMovimiento=None,
                detalles=[
                    EstadisticasModelosDetalle(
                        TipoOperacion=detalle.tipo_operacion,
                        NombreModelo=detalle.nombre_modelo,
                        InputTokens=detalle.input_tokens,
                        OutputTokens=detalle.output_tokens,
                        ThoughtsTokens=detalle.thoughts_tokens,
                        TotalTokens=detalle.total_tokens,
                    )
                    for detalle in valores_reg.detalles
                ],
                imagenes=[
                    EstadisticasModelosImagenes(
                        UrlTemporal=imagen.url_temporal,
                        UrlsPermanente=imagen.urls_permanente,
                        TamañoImagen=imagen.tamano_imagen,
                    )
                    for imagen in valores_reg.imagenes
                ],
            )

            db.add(nuevo_stats)
            await db.commit()
            await db.refresh(nuevo_stats)

            return RespuestaFuncion(data_registro=nuevo_stats.Id)

        except Exception as error:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=str(error),
            )
        # finally:
        #     print(time.perf_counter() - inicio)


async def actualizar_stast(valores_upd: ActualizarEstadisticas):
    # inicio = time.perf_counter()
    async with AsyncSessionLocal() as db:
        try:
            estadistica = await db.scalar(
                select(EstadisticasModelos)
                .options(selectinload(EstadisticasModelos.imagenes))
                .where(EstadisticasModelos.Id == valores_upd.id)
            )

            if estadistica is None:
                return RespuestaFuncion(
                    success_registro=False,
                    mensaje="No se encontró la estadística indicada.",
                )

            estadistica.Estado = valores_upd.estado
            estadistica.IdMovimiento=valores_upd.id_movimiento
            if valores_upd.estado == EstadoEstadisticaEnum.Registrada:
                imagenes_por_url = {
                    imagen.url_temporal: imagen.urls_permanente
                    for imagen in valores_upd.imagenes
                }
                for imagen in estadistica.imagenes:
                    if imagen.UrlTemporal in imagenes_por_url:
                        imagen.UrlsPermanente = imagenes_por_url[imagen.UrlTemporal]

            await db.commit()

            return RespuestaFuncion(data_registro=estadistica.Id)
        except Exception as error:
            
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=str(error),
            )




async def datos_errores_modelos(db: AsyncSession):
    try:
        result = await db.execute(
                select(ErroresModelos).order_by(ErroresModelos.Proceso.asc())
            )
        errores = result.scalars().all()
        
        return RespuestaFuncion(data_registro=errores)

    except Exception as error:
        await db.rollback()
        return RespuestaFuncion(
            success_registro=False,
            mensaje=str(error),
        )