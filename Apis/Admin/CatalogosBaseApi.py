from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from Repositories.catalogos_base_repo import obtener_catalogos_base
from Schemas.ApisResponseSchemas.datos_calagos_base_response_schema import CatalogosBaseResponse
from Config.settings import get_db

from .router_admin import generar_router_admin


router_catalogos_base = generar_router_admin('data-catalogos-base')







@router_catalogos_base.get("/lista-catalogos-base",response_model=CatalogosBaseResponse)
async def listar_canales(db: AsyncSession = Depends(get_db)):
    try:
        datos = await obtener_catalogos_base(db)
            
        return datos.data_registro
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al listar los canales de pago: {str(error)}",
        )