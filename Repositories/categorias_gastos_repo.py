from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.CategoriasGastos import CategoriasGastos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd

async def listar_categorias(db: AsyncSession):
    """Devuelve todas las categorías ordenadas por la más reciente."""
    result = await db.execute(
        select(CategoriasGastos)
        .order_by(CategoriasGastos.Id.desc())
    )
    return result.scalars().all()


async def registrar(db: AsyncSession, categoria: dict):
    """Registra o actualiza una categoría.

    categoria debe incluir:
    {id, nombre}
    """
    try:
        if not categoria:
            return RespuestaFuncion(success_registro=False, mensaje="Datos de la categoría no proporcionados")

        categoria_id = categoria.get("id", 0) or 0
        nombre = str(categoria.get("nombre", "")).strip()

        

        if not nombre:
            return RespuestaFuncion(success_registro=False, mensaje="El nombre de la categoría es obligatorio")

        if categoria_id > 0:
            result = await db.execute(
                select(CategoriasGastos).where(
                    CategoriasGastos.Id == categoria_id,
                    
                )
            )
            registro = result.scalars().first()
            if not registro:
                return RespuestaFuncion(success_registro=False, mensaje=f"Categoría con id {categoria_id} no encontrada")

            registro.NombreCategoria = nombre
            await db.commit()
            await db.refresh(registro)
            return RespuestaFuncion()

        categoria_existente = await db.execute(
            select(CategoriasGastos).where(
                
                CategoriasGastos.NombreCategoria == nombre,
            )
        )
        if categoria_existente.scalars().first():
            return RespuestaFuncion(success_registro=False, mensaje="Ya existe una categoría con ese nombre ")

        nueva_categoria = CategoriasGastos(
            
            NombreCategoria=nombre,
        )

        db.add(nueva_categoria)
        await db.commit()
        await db.refresh(nueva_categoria)
        return RespuestaFuncion(data_registro=nueva_categoria)

    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def obtener_categoria(db: AsyncSession, categoria_id: int):
    result = await db.execute(
        select(CategoriasGastos).where(
            CategoriasGastos.Id == categoria_id,
        )
    )
    return result.scalars().first()


async def eliminar_categoria(db: AsyncSession, categoria_id: int):
    if not categoria_id:
        return RespuestaFuncion(success_registro=False, mensaje="La categoría es obligatoria")

    categoria = await obtener_categoria(db, categoria_id)
    if not categoria:
        return RespuestaFuncion(success_registro=False, mensaje=f"Categoría con id {categoria_id} no encontrada")
    try:
        await db.delete(categoria)
        await db.commit()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    return RespuestaFuncion()
