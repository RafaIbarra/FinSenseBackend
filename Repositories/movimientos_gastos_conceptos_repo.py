from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.MovimientosGastosConceptos import MovimientosGastosConceptos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_conceptos_movimiento(db: AsyncSession, movimiento_id: int):
    result = await db.execute(
        select(MovimientosGastosConceptos)
        .where(MovimientosGastosConceptos.MovimientoGastoId == movimiento_id)
        .order_by(MovimientosGastosConceptos.Id.desc())
    )
    return result.scalars().all()


async def asociar_concepto(db: AsyncSession, movimiento_id: int, concepto_id: int):
    if not movimiento_id or not concepto_id:
        return RespuestaFuncion(
            success_registro=False,
            mensaje="El movimiento y el concepto son obligatorios",
        )

    existente = await db.execute(
        select(MovimientosGastosConceptos).where(
            MovimientosGastosConceptos.MovimientoGastoId == movimiento_id,
            MovimientosGastosConceptos.ConceptoId == concepto_id,
        )
    )
    if existente.scalars().first():
        return RespuestaFuncion(
            success_registro=False,
            mensaje="El concepto ya está asociado al movimiento",
        )

    try:
        asociacion = MovimientosGastosConceptos(
            MovimientoGastoId=movimiento_id,
            ConceptoId=concepto_id,
        )
        db.add(asociacion)
        await db.commit()
        await db.refresh(asociacion)
        return RespuestaFuncion(data_registro=asociacion)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def eliminar_concepto(db: AsyncSession, movimiento_id: int, concepto_id: int):
    result = await db.execute(
        select(MovimientosGastosConceptos).where(
            MovimientosGastosConceptos.MovimientoGastoId == movimiento_id,
            MovimientosGastosConceptos.ConceptoId == concepto_id,
        )
    )
    asociacion = result.scalars().first()
    if not asociacion:
        return RespuestaFuncion(
            success_registro=False,
            mensaje="El concepto no está asociado al movimiento",
        )

    try:
        await db.delete(asociacion)
        await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
