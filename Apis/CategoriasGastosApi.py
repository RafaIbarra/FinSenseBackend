from fastapi import Depends, Form, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from Common.routers_factory import generar_router
from Config.settings import get_db
from Repositories.categorias_gastos_repo import (
    eliminar_categoria,
    listar_categorias,
    obtener_categoria,
    registrar,
)

router_categorias = generar_router('/categorias')


@router_categorias.get("/listar")
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    categorias = await listar_categorias(db)

    return {
        "status": "success",
        "categorias": [
            {
                "id": categoria.Id,
                "nombre": categoria.NombreCategoria,
                "fecha_registro": categoria.FechaRegistro.isoformat() if categoria.FechaRegistro else None,
            }
            for categoria in categorias
        ],
    }


@router_categorias.get("/detalle/{categoria_id}")
async def detalle(
    request: Request,
    categoria_id: int,
    db: AsyncSession = Depends(get_db),
):
    categoria = await obtener_categoria(db, categoria_id)

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    return {
        "status": "success",
        "id": categoria.Id,
        "nombre": categoria.NombreCategoria,
        "fecha_registro": categoria.FechaRegistro.isoformat() if categoria.FechaRegistro else None,
    }


@router_categorias.post("/registro")
async def registro_categoria(
    request: Request,
    nombre: str = Form(...),
    id: int = Form(0),
    db: AsyncSession = Depends(get_db),
):
    categoria_data = {
        "id": id,
        "nombre": nombre,
    }

    resultado = await registrar(db, categoria_data)
    if isinstance(resultado, dict) and resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return {
        "status": "success",
        "id": resultado.Id,
        "nombre": resultado.NombreCategoria,
        "fecha_registro": resultado.FechaRegistro.isoformat() if resultado.FechaRegistro else None,
    }


@router_categorias.post("/eliminar")
async def eliminar(
    request: Request,
    id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    resultado = await eliminar_categoria(db, id)

    if isinstance(resultado, dict) and resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return resultado
