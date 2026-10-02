from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from Models.EntidadesUsuarios import EntidadesUsuarios
from Models.MarcasTarjetas import MarcasTarjetas
from Models.MediosPagosUsuarios import MediosPagosUsuarios
from Models.TiposMediosPagos import TiposMediosPagos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_medios_pagos_usuario(db: AsyncSession, id_usuario: int):
	if id_usuario <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario es obligatorio",
		)

	try:
		resultado = await db.execute(
			select(MediosPagosUsuarios)
			.options(
				selectinload(MediosPagosUsuarios.tipo_medio_pago),
				selectinload(MediosPagosUsuarios.entidad_usuario),
				selectinload(MediosPagosUsuarios.marca_tarjeta),
			)
			.where(MediosPagosUsuarios.UsuarioId == id_usuario)
			.order_by(MediosPagosUsuarios.Id.desc())
		)
		return RespuestaFuncion(data_registro=resultado.scalars().all())
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def crear_medio_pago_usuario(
	db: AsyncSession,
	id_usuario: int,
	tipo_medio_pago_id: int,
	entidad_usuario_id: Optional[int] = None,
	marca_tarjeta_id: Optional[int] = None,
):
	if id_usuario <= 0 or tipo_medio_pago_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario y el tipo de medio de pago son obligatorios",
		)

	try:
		error_validacion = await _validar_referencias_medio_pago(
			db,
			id_usuario,
			tipo_medio_pago_id,
			entidad_usuario_id,
			marca_tarjeta_id,
		)
		if error_validacion:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=error_validacion,
			)

		medio_existente = await db.execute(
			select(MediosPagosUsuarios.Id).where(
				MediosPagosUsuarios.UsuarioId == id_usuario,
				MediosPagosUsuarios.TipoMedioPagoId == tipo_medio_pago_id,
				MediosPagosUsuarios.EntidadUsuarioId == entidad_usuario_id,
				MediosPagosUsuarios.MarcaTarjetaId == marca_tarjeta_id,
			)
		)
		if medio_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="Ya existe un medio de pago con esos datos para el usuario",
			)

		medio_pago = MediosPagosUsuarios(
			UsuarioId=id_usuario,
			TipoMedioPagoId=tipo_medio_pago_id,
			EntidadUsuarioId=entidad_usuario_id,
			MarcaTarjetaId=marca_tarjeta_id,
			IsActive=True,
		)
		db.add(medio_pago)
		await db.commit()
		await db.refresh(medio_pago)
		return RespuestaFuncion(data_registro=medio_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def editar_medio_pago_usuario(
	db: AsyncSession,
	id_usuario: int,
	medio_pago_usuario_id: int,
	tipo_medio_pago_id: int,
	entidad_usuario_id: Optional[int] = None,
	marca_tarjeta_id: Optional[int] = None,
):
	if id_usuario <= 0 or medio_pago_usuario_id <= 0 or tipo_medio_pago_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario, el medio de pago y el tipo son obligatorios",
		)

	try:
		medio_pago = await _obtener_medio_pago_usuario(
			db,
			id_usuario,
			medio_pago_usuario_id,
		)
		if not medio_pago:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="El medio de pago no existe para este usuario",
			)

		error_validacion = await _validar_referencias_medio_pago(
			db,
			id_usuario,
			tipo_medio_pago_id,
			entidad_usuario_id,
			marca_tarjeta_id,
		)
		if error_validacion:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=error_validacion,
			)

		medio_existente = await db.execute(
			select(MediosPagosUsuarios.Id).where(
				MediosPagosUsuarios.UsuarioId == id_usuario,
				MediosPagosUsuarios.Id != medio_pago_usuario_id,
				MediosPagosUsuarios.TipoMedioPagoId == tipo_medio_pago_id,
				MediosPagosUsuarios.EntidadUsuarioId == entidad_usuario_id,
				MediosPagosUsuarios.MarcaTarjetaId == marca_tarjeta_id,
			)
		)
		if medio_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="Ya existe otro medio de pago con esos datos para el usuario",
			)

		medio_pago.TipoMedioPagoId = tipo_medio_pago_id
		medio_pago.EntidadUsuarioId = entidad_usuario_id
		medio_pago.MarcaTarjetaId = marca_tarjeta_id
		await db.commit()
		await db.refresh(medio_pago)
		return RespuestaFuncion(data_registro=medio_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def activar_medio_pago_usuario(
	db: AsyncSession,
	id_usuario: int,
	medio_pago_usuario_id: int,
):
	return await _cambiar_estado_medio_pago_usuario(
		db,
		id_usuario,
		medio_pago_usuario_id,
		True,
	)


async def desactivar_medio_pago_usuario(
	db: AsyncSession,
	id_usuario: int,
	medio_pago_usuario_id: int,
):
	return await _cambiar_estado_medio_pago_usuario(
		db,
		id_usuario,
		medio_pago_usuario_id,
		False,
	)


async def _obtener_medio_pago_usuario(
	db: AsyncSession,
	id_usuario: int,
	medio_pago_usuario_id: int,
):
	resultado = await db.execute(
		select(MediosPagosUsuarios).where(
			MediosPagosUsuarios.Id == medio_pago_usuario_id,
			MediosPagosUsuarios.UsuarioId == id_usuario,
		)
	)
	return resultado.scalars().first()


async def _validar_referencias_medio_pago(
	db: AsyncSession,
	id_usuario: int,
	tipo_medio_pago_id: int,
	entidad_usuario_id: Optional[int],
	marca_tarjeta_id: Optional[int],
) -> Optional[str]:
	resultado_tipo = await db.execute(
		select(TiposMediosPagos).where(TiposMediosPagos.Id == tipo_medio_pago_id)
	)
	tipo_medio_pago = resultado_tipo.scalars().first()
	if not tipo_medio_pago:
		return "El tipo de medio de pago no existe"

	if tipo_medio_pago.SolicitarEntidad and not entidad_usuario_id:
		return "Este tipo de medio de pago requiere una entidad"
	if entidad_usuario_id is not None:
		resultado_entidad = await db.execute(
			select(EntidadesUsuarios.Id).where(
				EntidadesUsuarios.Id == entidad_usuario_id,
				EntidadesUsuarios.UsuarioId == id_usuario,
				EntidadesUsuarios.IsActive.is_(True),
			)
		)
		if resultado_entidad.scalar_one_or_none() is None:
			return "La entidad no existe, está inactiva o no pertenece al usuario"

	if tipo_medio_pago.SolicitarMarca and not marca_tarjeta_id:
		return "Este tipo de medio de pago requiere una marca de tarjeta"
	if marca_tarjeta_id is not None:
		resultado_marca = await db.execute(
			select(MarcasTarjetas.Id).where(
				MarcasTarjetas.Id == marca_tarjeta_id,
				MarcasTarjetas.UsuarioId == id_usuario,
				MarcasTarjetas.IsActive.is_(True),
			)
		)
		if resultado_marca.scalar_one_or_none() is None:
			return "La marca no existe, está inactiva o no pertenece al usuario"

	return None


async def _cambiar_estado_medio_pago_usuario(
	db: AsyncSession,
	id_usuario: int,
	medio_pago_usuario_id: int,
	is_active: bool,
):
	if id_usuario <= 0 or medio_pago_usuario_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El usuario y el medio de pago son obligatorios",
		)

	try:
		medio_pago = await _obtener_medio_pago_usuario(
			db,
			id_usuario,
			medio_pago_usuario_id,
		)
		if not medio_pago:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="El medio de pago no existe para este usuario",
			)

		medio_pago.IsActive = is_active
		await db.commit()
		await db.refresh(medio_pago)
		return RespuestaFuncion(data_registro=medio_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)
