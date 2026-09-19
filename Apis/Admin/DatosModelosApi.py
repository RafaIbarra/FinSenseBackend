from fastapi import Depends, Form, HTTPException, Request, Query,status
from Config.settings import get_db,settings
from sqlalchemy.ext.asyncio import AsyncSession
from Integrations.groq_clasificador import disponibilidad
from Repositories.datos_modelos_repo import datos_errores_modelos
from Repositories.estadisticas_modelos_queries import datos_estadisticas_modelos
from Schemas.ApisResponseSchemas.estadisticas_modelos_response_schema import EstadisticasModelosResponse
from Schemas.ApisResponseSchemas.errores_modelos_schemas import ErroresModelosResponse
from Schemas.Respuestas import PaginatedResponse
from .router_admin import generar_router_admin
import math
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
@router_models.get("/errores-modelos", response_model=PaginatedResponse[ErroresModelosResponse])
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Registros por página"),
):
    try:
        datos = await datos_errores_modelos(db, page=page, page_size=page_size)

        if not datos.success_registro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=datos.mensaje,
            )

        total = datos.data_registro["total"]
        items = datos.data_registro["items"]
        total_pages = math.ceil(total / page_size) if total else 0

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}")

    
@router_models.get("/stats-models",response_model=list[EstadisticasModelosResponse])
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