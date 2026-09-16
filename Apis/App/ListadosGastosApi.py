from fastapi import Depends, HTTPException, Request,status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import get_db
# from Common.routers_factory import generar_router
from .router_app import generar_router_app_privada
from Common.rate_limit_middleware import rate_limit
from Repositories.gastos_queries import movimientos_usuario_gastos,listar_imagenes_pendientes_usuario,dashboard_usuario,datos_iva_mes
from Services.envio_archivo_services import generar_y_enviar_excel_iva
router_movimientos_listados = generar_router_app_privada('gastos-listados')

@router_movimientos_listados.get("/movimientos-usuario")
async def listar_movimiento_usuario(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario_id = int(request.state.id_usuario)
    datos = await movimientos_usuario_gastos(db,usuario_id)
    
    return datos



@router_movimientos_listados.get("/gastos-mes")
async def listar_movimiento_usuario(
    request: Request,
    anno: int,
    mes: int,
    db: AsyncSession = Depends(get_db),
):
    usuario_id = int(request.state.id_usuario)
    datos = await movimientos_usuario_gastos(db,usuario_id, mes, anno)
    
    return datos
        
    
@router_movimientos_listados.get("/pendientes-usuario")
async def listar_imagens_usuario(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    
    usuario_id = int(request.state.id_usuario)
    datos = await listar_imagenes_pendientes_usuario(db,usuario_id)
    
    return {
        
        "datos":datos
    }


@router_movimientos_listados.get("/dashboard-usuario")
@rate_limit(max_requests=5, window_seconds=60)
async def estadisticas(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario_id = int(request.state.id_usuario)
    ahora = datetime.now()
    año_actual = ahora.year
    mes_actual = ahora.month -1
    
    # Pasar los parámetros a la función
    datos = await dashboard_usuario(db, usuario_id, año_actual, mes_actual)
    
    
    return {
        
        "datos":datos
    }

@router_movimientos_listados.get("/excel-iva-mes")
async def generar_excel_iva_mes(
    request: Request,
    anno: int,
    mes: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        usuario_id = int(request.state.id_usuario)
        resultado = await generar_y_enviar_excel_iva(db, mes,anno,usuario_id)
        
        if not resultado.success_registro:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=resultado.mensaje,)
        
        return {"detail": resultado.mensaje}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error solicitud archvio: {str(e)}"
        )

