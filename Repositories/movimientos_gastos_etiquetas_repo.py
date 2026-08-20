from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.MovimientosGastosEtiquetas import MovimientosGastosEtiquetas
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_etiquetas_movimiento(db: AsyncSession, movimiento_id: int):
    result = await db.execute(
        select(MovimientosGastosEtiquetas)
        .where(MovimientosGastosEtiquetas.MovimientoGastoId == movimiento_id)
        .order_by(MovimientosGastosEtiquetas.Id.desc())
    )
    return result.scalars().all()


async def asociar_etiqueta(db: AsyncSession, movimiento_id: int, etiqueta_id: int):
    if not movimiento_id or not etiqueta_id:
        return RespuestaFuncion(
            success_registro=False,
            mensaje="El movimiento y la etiqueta son obligatorios",
        )

    existente = await db.execute(
        select(MovimientosGastosEtiquetas).where(
            MovimientosGastosEtiquetas.MovimientoGastoId == movimiento_id,
            MovimientosGastosEtiquetas.EtiquetaId == etiqueta_id,
        )
    )
    if existente.scalars().first():
        return RespuestaFuncion(
            success_registro=False,
            mensaje="La etiqueta ya está asociada al movimiento",
        )

    try:
        asociacion = MovimientosGastosEtiquetas(
            MovimientoGastoId=movimiento_id,
            EtiquetaId=etiqueta_id,
        )
        db.add(asociacion)
        await db.commit()
        await db.refresh(asociacion)
        return RespuestaFuncion(data_registro=asociacion)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def eliminar_etiqueta(db: AsyncSession, movimiento_id: int, etiqueta_id: int):
    result = await db.execute(
        select(MovimientosGastosEtiquetas).where(
            MovimientosGastosEtiquetas.MovimientoGastoId == movimiento_id,
            MovimientosGastosEtiquetas.EtiquetaId == etiqueta_id,
        )
    )
    asociacion = result.scalars().first()
    if not asociacion:
        return RespuestaFuncion(
            success_registro=False,
            mensaje="La etiqueta no está asociada al movimiento",
        )

    try:
        await db.delete(asociacion)
        await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
