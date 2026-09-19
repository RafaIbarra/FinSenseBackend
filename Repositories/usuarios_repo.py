from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from Models.EstadisticasModelos import EstadisticasModelos
from Models.MovimientosGastos import MovimientosGastos
from Models.Usuarios import Usuarios
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd

async def datos_usuarios_resumen(db: AsyncSession):
    try:
        result = await db.execute(
            select(Usuarios).options(
                selectinload(Usuarios.estadisticas_modelos)
                    .selectinload(EstadisticasModelos.detalles),
                selectinload(Usuarios.imagenes_pendientes),
                selectinload(Usuarios.imagenes_reportadas),
                selectinload(Usuarios.movimientos_gastos)
                    .selectinload(MovimientosGastos.imagenes),
                selectinload(Usuarios.sesiones_activas),
            )
        )
        usuarios = result.scalars().all()

        return RespuestaFuncion(data_registro=usuarios)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))