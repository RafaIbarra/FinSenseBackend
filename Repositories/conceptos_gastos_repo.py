from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.ConceptosGastos import ConceptosGastos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_conceptos(db: AsyncSession):
    result = await db.execute(
        select(ConceptosGastos)
        .order_by(ConceptosGastos.Id.desc())
    )
    return result.scalars().all()


async def registrar_conceptos_masivo(db: AsyncSession, nombres: list[str]):
    if not nombres:
        return RespuestaFuncion(data_registro=[])

    nuevos_conceptos = [
        ConceptosGastos(NombreConcepto=nombre)
        for nombre in nombres
    ]
    db.add_all(nuevos_conceptos)
    await db.flush()

    return RespuestaFuncion(data_registro=nuevos_conceptos)


async def obtener_o_crear_conceptos(db: AsyncSession, nombres: list[str]):
    nombres_normalizados = {
        nombre.strip()
        for nombre in nombres
        if nombre and nombre.strip()
    }
    if not nombres_normalizados:
        return RespuestaFuncion(data_registro=[])

    result = await db.execute(
        select(ConceptosGastos).where(
            func.lower(ConceptosGastos.NombreConcepto).in_(
                [nombre.lower() for nombre in nombres_normalizados]
            )
        )
    )
    conceptos = list(result.scalars().all())
    nombres_existentes = {concepto.NombreConcepto.lower() for concepto in conceptos}
    nombres_faltantes = [
        nombre for nombre in nombres_normalizados
        if nombre.lower() not in nombres_existentes
    ]

    if nombres_faltantes:
        nuevos = [ConceptosGastos(NombreConcepto=nombre) for nombre in nombres_faltantes]
        db.add_all(nuevos)
        await db.flush()
        conceptos.extend(nuevos)

    return RespuestaFuncion(data_registro=[concepto.Id for concepto in conceptos])


async def registrar_concepto(db: AsyncSession, concepto: dict):
    try:
        if not concepto:
            return RespuestaFuncion(success_registro=False, mensaje="Datos del concepto no proporcionados")

        concepto_id = concepto.get("id", 0) or 0
        nombre = str(concepto.get("nombre", "")).strip()

        if not nombre:
            return RespuestaFuncion(success_registro=False, mensaje="El nombre del concepto es obligatorio")

        if concepto_id > 0:
            result = await db.execute(
                select(ConceptosGastos).where(
                    ConceptosGastos.Id == concepto_id,
                )
            )
            registro = result.scalars().first()
            if not registro:
                return RespuestaFuncion(success_registro=False, mensaje=f"Concepto con id {concepto_id} no encontrado")

            registro.NombreConcepto = nombre
            await db.commit()
            await db.refresh(registro)
            return RespuestaFuncion(data_registro=registro)

        existente = await db.execute(
            select(ConceptosGastos).where(
                func.lower(ConceptosGastos.NombreConcepto) == func.lower(nombre),
            )
        )
        if existente.scalars().first():
            return RespuestaFuncion(success_registro=False, mensaje="Ya existe un concepto con ese nombre")

        nuevo_concepto = ConceptosGastos(
            NombreConcepto=nombre,
        )
        db.add(nuevo_concepto)
        await db.commit()
        await db.refresh(nuevo_concepto)
        return RespuestaFuncion(data_registro=nuevo_concepto)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def obtener_concepto(db: AsyncSession, concepto_id: int):
    result = await db.execute(
        select(ConceptosGastos).where(
            ConceptosGastos.Id == concepto_id,
        )
    )
    return result.scalars().first()


async def eliminar_concepto(db: AsyncSession, concepto_id: int):
    if not concepto_id:
        return RespuestaFuncion(success_registro=False, mensaje="El concepto es obligatorio")

    concepto = await obtener_concepto(db, concepto_id)
    if not concepto:
        return RespuestaFuncion(success_registro=False, mensaje=f"Concepto con id {concepto_id} no encontrado")
    try:
        await db.delete(concepto)
        await db.commit()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    return RespuestaFuncion()