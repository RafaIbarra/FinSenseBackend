from fastapi import Depends, Form, HTTPException, Request, Response,status,File, UploadFile
from Config.settings import get_db,settings
from sqlalchemy.ext.asyncio import AsyncSession
from Integrations.groq_clasificador import disponibilidad
from Repositories.datos_modelos_repo import datos_errores_modelos
from Repositories.estadisticas_modelos_queries import datos_estadisticas_modelos

from .router_admin import generar_router_admin

router_models = generar_router_admin('models')


@router_models.get("/groq")
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    modelos = await disponibilidad()
    
    return {
        "status": "success",
        "empresas":modelos
    }
@router_models.get("/errores-modelos")
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:    
        datos= await datos_errores_modelos(db)
        
        return datos.data_registro
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}")

    
@router_models.get("/stats-models")
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:    
        datos= await datos_estadisticas_modelos(db)
        
        return datos.data_registro
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}")