from fastapi import Depends,  Request
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import get_db
from Common.routers_factory import generar_router
from Repositories.gastos_queries import movimientos_usuario_gastos,listar_imagenes_pendientes_usuario,dashboard_usuario

router_movimientos_listados = generar_router('/gastos-listados')
@router_movimientos_listados.get("/movimientos-usuario")
async def listar_movimiento_usuario(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario_id = int(request.state.id_usuario)
    datos = await movimientos_usuario_gastos(db,usuario_id)
    
    return {
        
        "datos":datos
    }
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
async def estadisticas(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario_id = int(request.state.id_usuario)
    ahora = datetime.now()
    año_actual = ahora.year
    mes_actual = ahora.month

    # Pasar los parámetros a la función
    datos = await dashboard_usuario(db, usuario_id, año_actual, mes_actual)
    
    return {
        
        "datos":datos
    }
