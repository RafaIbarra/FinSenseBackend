from fastapi import Depends, Form, HTTPException, Request, Query,status
from Config.settings import get_db,settings
from sqlalchemy.ext.asyncio import AsyncSession
from Repositories.usuarios_repo import datos_usuarios_resumen
from Schemas.ApisResponseSchemas.datos_usuarios_response_schema import UsuarioResumenResponse

from .router_admin import generar_router_admin

router_admin_users = generar_router_admin('users')
@router_admin_users.get("/data-users",response_model=list[UsuarioResumenResponse])
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:    
        datos= await datos_usuarios_resumen(db)
        
        return datos.data_registro
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro factura: {str(e)}")