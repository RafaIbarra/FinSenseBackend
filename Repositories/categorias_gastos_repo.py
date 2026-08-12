from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.CategoriasGastos import CategoriasGastos


async def listar_categorias(db: AsyncSession, usuario_id: int):
    """Devuelve todas las categorías del usuario ordenadas por la más reciente."""
    result = await db.execute(
        select(CategoriasGastos)
        .where(CategoriasGastos.UsuarioId == usuario_id)
        .order_by(CategoriasGastos.Id.desc())
    )
    return result.scalars().all()


async def registrar(db: AsyncSession, categoria: dict):
    """Registra o actualiza una categoría del usuario.

    categoria debe incluir:
    {id, user_id, nombre}
    """
    try:
        if not categoria:
            return {"error": "Datos de la categoría no proporcionados"}

        categoria_id = categoria.get("id", 0) or 0
        usuario_id = categoria.get("user_id")
        nombre = str(categoria.get("nombre", "")).strip()

        if not usuario_id:
            return {"error": "El usuario es obligatorio"}

        if not nombre:
            return {"error": "El nombre de la categoría es obligatorio"}

        if categoria_id > 0:
            result = await db.execute(
                select(CategoriasGastos).where(
                    CategoriasGastos.Id == categoria_id,
                    CategoriasGastos.UsuarioId == usuario_id,
                )
            )
            registro = result.scalars().first()
            if not registro:
                return {"error": f"Categoría con id {categoria_id} no encontrada para el usuario"}

            registro.NombreCategoria = nombre
            await db.commit()
            await db.refresh(registro)
            return registro

        categoria_existente = await db.execute(
            select(CategoriasGastos).where(
                CategoriasGastos.UsuarioId == usuario_id,
                CategoriasGastos.NombreCategoria == nombre,
            )
        )
        if categoria_existente.scalars().first():
            return {"error": "Ya existe una categoría con ese nombre para este usuario"}

        nueva_categoria = CategoriasGastos(
            UsuarioId=usuario_id,
            NombreCategoria=nombre,
        )

        db.add(nueva_categoria)
        await db.commit()
        await db.refresh(nueva_categoria)
        return nueva_categoria

    except Exception as e:
        await db.rollback()
        return {"error": str(e)}


async def obtener_categoria(db: AsyncSession, categoria_id: int, usuario_id: int):
    result = await db.execute(
        select(CategoriasGastos).where(
            CategoriasGastos.Id == categoria_id,
            CategoriasGastos.UsuarioId == usuario_id,
        )
    )
    return result.scalars().first()


async def eliminar_categoria(db: AsyncSession, categoria_id: int, usuario_id: int):
    if not categoria_id:
        return {"error": "La categoría es obligatoria"}

    categoria = await obtener_categoria(db, categoria_id, usuario_id)
    if not categoria:
        return {"error": f"Categoría con id {categoria_id} no encontrada para el usuario"}

    await db.delete(categoria)
    await db.commit()
    return {"status": "success", "id": categoria_id, "deleted": True}
