from fastapi import Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from Common.routers_factory import generar_router
from Config.settings import get_db
from Repositories.envio_correo_repo import listado_envios_correo
from Repositories.imagenes_pendientes_repo import listado_imagenes_pendientes
from Repositories.imagenes_reportadas_repo import listado_reportados
router_admin = generar_router('/admin',protegido_admin=True)

@router_admin.get("/listado-envio-correo")
async def listar_correos(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        datos = await listado_envios_correo(db)
        return datos.data_registro
    except HTTPException:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}"
        )

    
@router_admin.get("/listado-imagenes-pendientes")
async def listar_img_pendientes(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        datos = await listado_imagenes_pendientes(db)
        return datos.data_registro
    except HTTPException:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}"
        )

@router_admin.get("/listado-imagenes-reportadas")
async def listar_img_reportadas(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        datos = await listado_reportados(db)
        return datos.data_registro
    except HTTPException:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}"
        )