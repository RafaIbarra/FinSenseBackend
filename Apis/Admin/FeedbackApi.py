from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import get_db
from .router_admin import generar_router_admin
from Repositories.imagenes_reportadas_repo import listado_reportados
from Schemas.ApisResponseSchemas.feedback_response_schema import ImagenesResportadasResponse



router_feedback_usuarios = generar_router_admin('feedback-usuarios')
@router_feedback_usuarios.get("/reportadas", response_model=list[ImagenesResportadasResponse])
async def lista_imaganes_reportadas(db: AsyncSession = Depends(get_db)):
    try:
        datos = await listado_reportados(db)
        print(datos.data_registro)
        return datos.data_registro
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al listar los canales de pago: {str(error)}",)