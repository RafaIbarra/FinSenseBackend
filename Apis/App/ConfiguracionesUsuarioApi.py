from fastapi import  Depends, Form, HTTPException,Request,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
# from Common.routers_factory import generar_router
from .router_app import generar_router_app_privada
from Config.settings import get_db
from Repositories.preferencia_usuario_repo import registrar_preferencia_usuario
from Repositories.temas_repo import listar_temas

# router_user_config = generar_router('/user-config', ["Preferencias Usuarios"])
router_user_config = generar_router_app_privada('user-config')

@router_user_config.post("/usuario-movile-theme")
async def asignar_tema_usuario(
    request: Request,
    tema: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        
        id_usuario = int(request.state.id_usuario)
        
        registro = await registrar_preferencia_usuario(db, id_usuario,tema)
        if not registro.success_registro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=registro.mensaje,
            )
        return {"detail": "Su preferencia fue procesada"}
        
    except HTTPException:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro preferencia: {str(e)}"
        )


@router_user_config.get("/temas")
async def listado_temas(
    
    db: AsyncSession = Depends(get_db),
):
    try:
        
        
        
        registro = await listar_temas(db)
        if not registro.success_registro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=registro.mensaje,
            )
        return registro.data_registro
        
    except HTTPException:
            raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro preferencia: {str(e)}"
        )