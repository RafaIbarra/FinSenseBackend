from sqlalchemy import func, select
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


async def registrar_etiquetas_masivo(db: AsyncSession, nombres: list[str]):
    if not nombres:
        return RespuestaFuncion(data_registro=[])

    nuevas_etiquetas = [
        EtiquetasGastos(NombreEtiqueta=nombre)
        for nombre in nombres
    ]
    db.add_all(nuevas_etiquetas)
    await db.flush()

    return RespuestaFuncion(data_registro=nuevas_etiquetas)


async def obtener_o_crear_etiquetas(db: AsyncSession, nombres: list[str]):
    nombres_normalizados = {
        nombre.strip()
        for nombre in nombres
        if nombre and nombre.strip()
    }
    if not nombres_normalizados:
        return RespuestaFuncion(data_registro=[])

    result = await db.execute(
        select(EtiquetasGastos).where(
            func.lower(EtiquetasGastos.NombreEtiqueta).in_(
                [nombre.lower() for nombre in nombres_normalizados]
            )
        )
    )
    etiquetas = list(result.scalars().all())
    nombres_existentes = {etiqueta.NombreEtiqueta.lower() for etiqueta in etiquetas}
    nombres_faltantes = [
        nombre for nombre in nombres_normalizados
        if nombre.lower() not in nombres_existentes
    ]

    if nombres_faltantes:
        nuevas = [EtiquetasGastos(NombreEtiqueta=nombre) for nombre in nombres_faltantes]
        db.add_all(nuevas)
        await db.flush()
        etiquetas.extend(nuevas)

    return RespuestaFuncion(data_registro=[etiqueta.Id for etiqueta in etiquetas])


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
                func.lower(EtiquetasGastos.NombreEtiqueta) == func.lower(nombre),
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