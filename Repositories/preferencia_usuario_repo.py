from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.PreferenciasUsuario import PreferenciasUsuario
from Models.Temas import Temas
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def registrar_preferencia_usuario(
	db: AsyncSession,
	usuario_id: int,
	nombre_tema: str,
):
	"""Registra el tema preferido del usuario, reemplazando el anterior."""
	usuario_id = usuario_id or 0
	nombre_tema = str(nombre_tema or "").strip()

	if not usuario_id:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario es obligatorio",
		)
	if not nombre_tema:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre del tema es obligatorio",
		)

	try:
		resultado_tema = await db.execute(
			select(Temas).where(
				func.lower(Temas.NombreTema) == nombre_tema.lower(),
			)
		)
		tema = resultado_tema.scalars().first()
		print(f'el temas es {tema}')
		if not tema:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Tema '{nombre_tema}' no encontrado",
			)

		resultado_preferencia = await db.execute(
			select(PreferenciasUsuario).where(
				PreferenciasUsuario.UsuarioId == usuario_id,
			)
		)
		preferencia_actual = resultado_preferencia.scalars().first()

		if preferencia_actual and preferencia_actual.TemaId == tema.Id:
			return RespuestaFuncion(data_registro=preferencia_actual)

		if preferencia_actual:
			await db.delete(preferencia_actual)
			await db.flush()

		nueva_preferencia = PreferenciasUsuario(
			UsuarioId=usuario_id,
			TemaId=tema.Id,
		)
		db.add(nueva_preferencia)
		await db.commit()
		await db.refresh(nueva_preferencia)
		return RespuestaFuncion(data_registro=nueva_preferencia)
	except Exception as exc:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(exc)),
		)

