from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.MarcasTarjetas import MarcasTarjetas
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_marcas_tarjetas(db: AsyncSession, id_usuario: int):
    try:
        if id_usuario <= 0:
            return RespuestaFuncion(
                success_registro=False,
                mensaje="El usuario es obligatorio",
            )

        resultado = await db.execute(
            select(MarcasTarjetas)
            .where(MarcasTarjetas.UsuarioId == id_usuario)
            .order_by(MarcasTarjetas.Id.desc())
        )
        data= resultado.scalars().all()
        return RespuestaFuncion(data_registro=data)
    except Exception as error:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=limpiar_mensaje_error_bd(str(error)),
            )

async def crear_marca_tarjeta(db: AsyncSession, id_usuario: int, nombre: str):
	nombre = str(nombre or "").strip()
	if id_usuario <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario es obligatorio",
		)
	if not nombre:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre de la marca es obligatorio",
		)

	try:
		marca_existente = await db.execute(
			select(MarcasTarjetas.Id).where(
				MarcasTarjetas.UsuarioId == id_usuario,
				func.lower(MarcasTarjetas.NombreMarca) == func.lower(nombre),
			)
		)
		if marca_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe una marca el nombre {nombre} para el usuario",
			)

		marca = MarcasTarjetas(
			NombreMarca=nombre,
			UsuarioId=id_usuario,
			IsActive=True,
		)
		db.add(marca)
		await db.commit()
		await db.refresh(marca)
		return RespuestaFuncion(data_registro=marca)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def editar_marca_tarjeta(
	db: AsyncSession,
	id_usuario: int,
	marca_id: int,
	nombre: str,
):
	nombre = str(nombre or "").strip()
	if id_usuario <= 0 or marca_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario y la marca son obligatorios",
		)
	if not nombre:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre de la marca es obligatorio",
		)

	marca = await _obtener_marca_usuario(db, id_usuario, marca_id)
	if not marca:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="La marca no existe para este usuario",
		)

	try:
		marca_existente = await db.execute(
			select(MarcasTarjetas.Id).where(
				MarcasTarjetas.UsuarioId == id_usuario,
				MarcasTarjetas.Id != marca_id,
				func.lower(MarcasTarjetas.NombreMarca) == func.lower(nombre),
			)
		)
		if marca_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe otra marca con el nombre {nombre} para el usuario",
			)

		marca.NombreMarca = nombre
		await db.commit()
		await db.refresh(marca)
		return RespuestaFuncion(data_registro=marca)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)

async def activar_marca_tarjeta(
	db: AsyncSession,
	id_usuario: int,
	marca_id: int,
):
	return await _cambiar_estado_marca_tarjeta(
		db,
		id_usuario,
		marca_id,
		True,
	)


async def desactivar_marca_tarjeta(
	db: AsyncSession,
	id_usuario: int,
	marca_id: int,
):
	return await _cambiar_estado_marca_tarjeta(
		db,
		id_usuario,
		marca_id,
		False,
	)




async def _obtener_marca_usuario(
	db: AsyncSession,
	id_usuario: int,
	marca_id: int,
):
	resultado = await db.execute(
		select(MarcasTarjetas).where(
			MarcasTarjetas.Id == marca_id,
			MarcasTarjetas.UsuarioId == id_usuario,
		)
	)
	return resultado.scalars().first()

async def _cambiar_estado_marca_tarjeta(
	db: AsyncSession,
	id_usuario: int,
	marca_id: int,
	is_active: bool,
):
	if id_usuario <= 0 or marca_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario y la marca son obligatorios",
		)

	marca = await _obtener_marca_usuario(db, id_usuario, marca_id)
	if not marca:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="La marca no existe para este usuario",
		)

	try:
		marca.IsActive = is_active
		await db.commit()
		await db.refresh(marca)
		return RespuestaFuncion(data_registro=marca)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)