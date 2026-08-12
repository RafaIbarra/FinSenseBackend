from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from Common.routers_factory import generar_router
from Config.settings import get_db
from Repositories.empresas_repo import (
    eliminar_empresa,
    listar_empresas,
    obtener_empresa,
    registrar,
)

router_empresas = generar_router('/empresas')


@router_empresas.get("/listar")
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    empresas = await listar_empresas(db)

    return {
        "status": "success",
        "empresas": [
            {
                "id": empresa.Id,
                "nombre": empresa.NombreEmpresa,
                "ruc": empresa.Ruc,
                "url_logo": empresa.UrlLogo,
                "fecha_registro": empresa.FechaRegistro.isoformat() if empresa.FechaRegistro else None,
            }
            for empresa in empresas
        ],
    }


@router_empresas.get("/detalle/{empresa_id}")
async def detalle(
    request: Request,
    empresa_id: int,
    db: AsyncSession = Depends(get_db),
):
    empresa = await obtener_empresa(db, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    return {
        "status": "success",
        "id": empresa.Id,
        "nombre": empresa.NombreEmpresa,
        "ruc": empresa.Ruc,
        "url_logo": empresa.UrlLogo,
        "fecha_registro": empresa.FechaRegistro.isoformat() if empresa.FechaRegistro else None,
    }


@router_empresas.post("/registro")
async def registro_empresa(
    request: Request,
    nombre: str = Form(...),
    ruc: str = Form(...),
    logo_img: UploadFile | None = File(None),
    id: int = Form(0),
    db: AsyncSession = Depends(get_db),
):
    empresa_data = {
        "id": id,
        "nombre": nombre,
        "ruc": ruc,
        "logo_img": logo_img,
    }

    resultado = await registrar(db, empresa_data)
    if isinstance(resultado, dict) and resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return {
        "status": "success",
        "id": resultado.Id,
        "nombre": resultado.NombreEmpresa,
        "ruc": resultado.Ruc,
        "url_logo": resultado.UrlLogo,
        "fecha_registro": resultado.FechaRegistro.isoformat() if resultado.FechaRegistro else None,
    }


@router_empresas.post("/eliminar")
async def eliminar(
    request: Request,
    id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    resultado = await eliminar_empresa(db, id)

    if isinstance(resultado, dict) and resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return resultado
