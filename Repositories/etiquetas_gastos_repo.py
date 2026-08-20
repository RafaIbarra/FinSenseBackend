from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.EtiquetasGastos import EtiquetasGastos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_etiquetas(db: AsyncSession):
    result = await db.execute(
        select(EtiquetasGastos)
        .order_by(EtiquetasGastos.Id.desc())
    )
    return result.scalars().all()


async def registrar_etiqueta(db: AsyncSession, etiqueta: dict):
    try:
        if not etiqueta:
            return RespuestaFuncion(success_registro=False, mensaje="Datos de la etiqueta no proporcionados")

        etiqueta_id = etiqueta.get("id", 0) or 0
        nombre = str(etiqueta.get("nombre", "")).strip()

        if not nombre:
            return RespuestaFuncion(success_registro=False, mensaje="El nombre de la etiqueta es obligatorio")

        if etiqueta_id > 0:
            result = await db.execute(
                select(EtiquetasGastos).where(
                    EtiquetasGastos.Id == etiqueta_id,
                )
            )
            registro = result.scalars().first()
            if not registro:
                return RespuestaFuncion(success_registro=False, mensaje=f"Etiqueta con id {etiqueta_id} no encontrada")

            registro.NombreEtiqueta = nombre
            await db.commit()
            await db.refresh(registro)
            return RespuestaFuncion(data_registro=registro)

        existente = await db.execute(
            select(EtiquetasGastos).where(
                EtiquetasGastos.NombreEtiqueta == nombre,
            )
        )
        if existente.scalars().first():
            return RespuestaFuncion(success_registro=False, mensaje="Ya existe una etiqueta con ese nombre")

        nueva_etiqueta = EtiquetasGastos(
            NombreEtiqueta=nombre,
        )
        db.add(nueva_etiqueta)
        await db.commit()
        await db.refresh(nueva_etiqueta)
        return RespuestaFuncion(data_registro=nueva_etiqueta)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def obtener_etiqueta(db: AsyncSession, etiqueta_id: int):
    result = await db.execute(
        select(EtiquetasGastos).where(
            EtiquetasGastos.Id == etiqueta_id,
        )
    )
    return result.scalars().first()


async def eliminar_etiqueta(db: AsyncSession, etiqueta_id: int):
    if not etiqueta_id:
        return RespuestaFuncion(success_registro=False, mensaje="La etiqueta es obligatoria")

    etiqueta = await obtener_etiqueta(db, etiqueta_id)
    if not etiqueta:
        return RespuestaFuncion(success_registro=False, mensaje=f"Etiqueta con id {etiqueta_id} no encontrada")
    try:
        await db.delete(etiqueta)
        await db.commit()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    return RespuestaFuncion()