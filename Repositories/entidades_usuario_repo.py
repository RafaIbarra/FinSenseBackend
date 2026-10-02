from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.EntidadesUsuarios import EntidadesUsuarios
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_entidades_usuario(db: AsyncSession, id_usuario: int):
	try:
		if id_usuario <= 0:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="El usuario es obligatorio",
			)

		resultado = await db.execute(
			select(EntidadesUsuarios)
			.where(EntidadesUsuarios.UsuarioId == id_usuario)
			.order_by(EntidadesUsuarios.Id.desc())
		)
		return RespuestaFuncion(data_registro=resultado.scalars().all())
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def crear_entidad_usuario(db: AsyncSession, id_usuario: int, nombre: str):
	nombre = str(nombre or "").strip()
	if id_usuario <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario es obligatorio",
		)
	if not nombre:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre de la entidad es obligatorio",
		)

	try:
		entidad_existente = await db.execute(
			select(EntidadesUsuarios.Id).where(
				EntidadesUsuarios.UsuarioId == id_usuario,
				func.lower(EntidadesUsuarios.NombreEntidad) == func.lower(nombre),
			)
		)
		if entidad_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe una entidad con el nombre {nombre} para el usuario",
			)

		entidad = EntidadesUsuarios(
			NombreEntidad=nombre,
			UsuarioId=id_usuario,
			IsActive=True,
		)
		db.add(entidad)
		await db.commit()
		await db.refresh(entidad)
		return RespuestaFuncion(data_registro=entidad)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def editar_entidad_usuario(
	db: AsyncSession,
	id_usuario: int,
	entidad_id: int,
	nombre: str,
):
	nombre = str(nombre or "").strip()
	if id_usuario <= 0 or entidad_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario y la entidad son obligatorios",
		)
	if not nombre:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre de la entidad es obligatorio",
		)

	entidad = await _obtener_entidad_usuario(db, id_usuario, entidad_id)
	if not entidad:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="La entidad no existe para este usuario",
		)

	try:
		entidad_existente = await db.execute(
			select(EntidadesUsuarios.Id).where(
				EntidadesUsuarios.UsuarioId == id_usuario,
				EntidadesUsuarios.Id != entidad_id,
				func.lower(EntidadesUsuarios.NombreEntidad) == func.lower(nombre),
			)
		)
		if entidad_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe otra entidad con el nombre {nombre} para el usuario",
			)

		entidad.NombreEntidad = nombre
		await db.commit()
		await db.refresh(entidad)
		return RespuestaFuncion(data_registro=entidad)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def activar_entidad_usuario(
	db: AsyncSession,
	id_usuario: int,
	entidad_id: int,
):
	return await _cambiar_estado_entidad_usuario(
		db,
		id_usuario,
		entidad_id,
		True,
	)


async def desactivar_entidad_usuario(
	db: AsyncSession,
	id_usuario: int,
	entidad_id: int,
):
	return await _cambiar_estado_entidad_usuario(
		db,
		id_usuario,
		entidad_id,
		False,
	)


async def _obtener_entidad_usuario(
	db: AsyncSession,
	id_usuario: int,
	entidad_id: int,
):
	resultado = await db.execute(
		select(EntidadesUsuarios).where(
			EntidadesUsuarios.Id == entidad_id,
			EntidadesUsuarios.UsuarioId == id_usuario,
		)
	)
	return resultado.scalars().first()


async def _cambiar_estado_entidad_usuario(
	db: AsyncSession,
	id_usuario: int,
	entidad_id: int,
	is_active: bool,
):
	if id_usuario <= 0 or entidad_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario y la entidad son obligatorios",
		)

	try:
		entidad = await _obtener_entidad_usuario(db, id_usuario, entidad_id)
		if not entidad:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="La entidad no existe para este usuario",
			)

		entidad.IsActive = is_active
		await db.commit()
		await db.refresh(entidad)
		return RespuestaFuncion(data_registro=entidad)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)
