
from sqlalchemy import  select
from sqlalchemy.orm import selectinload,load_only
from sqlalchemy.ext.asyncio import AsyncSession


from Models.ImagenesPendientes import ImagenesPendientes
from Models.MovimientosGastos import MovimientosGastos

from Models.Usuarios import Usuarios


from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd

async def datos_tareas(db: AsyncSession):
    try:
        result_img_pendientes = await db.execute(
            select(ImagenesPendientes)
            .options(
                selectinload(ImagenesPendientes.movimiento).load_only(MovimientosGastos.Id),

                selectinload(ImagenesPendientes.usuario).load_only(Usuarios.UserName))
            .order_by(ImagenesPendientes.Id.desc())
        )
        imagenes_pendientes = result_img_pendientes.scalars().all()
        return RespuestaFuncion(data_registro=imagenes_pendientes)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))