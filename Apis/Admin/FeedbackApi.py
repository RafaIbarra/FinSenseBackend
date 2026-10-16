from fastapi import Depends, HTTPException, status, Request, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import get_db
from .router_admin import generar_router_admin
from Repositories.imagenes_reportadas_repo import listado_reportados,registrar_resolucion_reporte
from Schemas.ApisResponseSchemas.feedback_response_schema import ImagenesResportadasResponse



router_feedback_usuarios = generar_router_admin('feedback-usuarios')
@router_feedback_usuarios.get("/reportadas", response_model=list[ImagenesResportadasResponse])
async def lista_imagenes_reportadas(
    request: Request,
    id_reporte: int | None = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db)):
    try:
        # id_usuario = int(request.state.id_usuario)
        datos = await listado_reportados(db,0,id_reporte or 0)
        
        return datos.data_registro
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al listar los canales de pago: {str(error)}",)
    


@router_feedback_usuarios.post("/resolver-reporte")
async def resolver_reporte(
    request: Request,
    id: int = Form(...),
    respuesta: str = Form(""),
    db: AsyncSession = Depends(get_db)):
    try:
        # id_usuario = int(request.state.id_usuario)
        resgistro = await registrar_resolucion_reporte(db,id,respuesta)
        
        if resgistro.success_registro:
            return {"detail": "Reporte resuelto"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resgistro.mensaje,
            )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar la resolucion: {str(error)}",)