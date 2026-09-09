from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from Schemas.Respuestas import RespuestaFuncion
from Models.Temas import Temas
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_temas(db: AsyncSession):
	"""Devuelve todos los temas ordenados por los más recientes."""
	try:
		resultado = await db.execute(
			select(Temas).order_by(Temas.Id.desc())
		)
		temas = resultado.scalars().all()
		data_registro = [
			{
				"Id": tema.Id,
				"NombreTema": tema.NombreTema,
				"Tipo": tema.Tipo,
				"Descripcion": tema.Descripcion,
				"FechaRegistro": tema.FechaRegistro.strftime("%d/%m/%Y %H:%M:%S"),
			}
			for tema in temas
		]
		return RespuestaFuncion(data_registro=data_registro)
	
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)
