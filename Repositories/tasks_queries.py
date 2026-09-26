
from sqlalchemy import  select
from sqlalchemy.orm import selectinload,load_only
from sqlalchemy.ext.asyncio import AsyncSession


from Models.ImagenesPendientes import ImagenesPendientes
from Models.MovimientosGastos import MovimientosGastos
from Models.EnvioCorreos import EnvioCorreos

from Models.Usuarios import Usuarios


from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd

async def obtener_datos_tareas(db: AsyncSession):
    try:
        imagenes_pendientes_qs = await db.execute(
            select(ImagenesPendientes)
            .options(
                selectinload(ImagenesPendientes.movimiento).load_only(MovimientosGastos.Id),

                selectinload(ImagenesPendientes.usuario).load_only(Usuarios.UserName))
            .order_by(ImagenesPendientes.Id.desc())
        )
        imagenes_pendientes_data = imagenes_pendientes_qs.scalars().all()

        envio_correos_qs = await db.execute(
                    select(EnvioCorreos)
                    .options(
                        
                        selectinload(EnvioCorreos.usuario).load_only(Usuarios.UserName))
                    .order_by(EnvioCorreos.Id.desc())
                )
        envio_correos_data = envio_correos_qs.scalars().all()
        valores={
            'imagenes_pendientes':imagenes_pendientes_data,
            'envio_correos':envio_correos_data
        }

        return RespuestaFuncion(data_registro=valores)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))