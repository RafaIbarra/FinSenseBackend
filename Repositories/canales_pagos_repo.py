from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.CanalesPagos import CanalesPagos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_canales_pagos(db: AsyncSession):
	try:
		resultado = await db.execute(
			select(CanalesPagos).order_by(CanalesPagos.Id.desc())
		)
		return RespuestaFuncion(data_registro=resultado.scalars().all())
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def crear_canal_pago(db: AsyncSession, nombre_canal: str):
	nombre_canal = str(nombre_canal or "").strip()
	if not nombre_canal:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre del canal de pago es obligatorio",
		)

	try:
		canal_existente = await db.execute(
			select(CanalesPagos.Id).where(
				func.lower(CanalesPagos.NombreCanal) == func.lower(nombre_canal),
			)
		)
		if canal_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe un canal de pago con el nombre {nombre_canal}",
			)

		canal_pago = CanalesPagos(NombreCanal=nombre_canal)
		db.add(canal_pago)
		await db.commit()
		await db.refresh(canal_pago)
		return RespuestaFuncion(data_registro=canal_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def editar_canal_pago(
	db: AsyncSession,
	canal_pago_id: int,
	nombre_canal: str,
):
	nombre_canal = str(nombre_canal or "").strip()
	if canal_pago_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El canal de pago es obligatorio",
		)
	if not nombre_canal:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre del canal de pago es obligatorio",
		)

	try:
		canal_pago = await _obtener_canal_pago(db, canal_pago_id)
		if not canal_pago:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="El canal de pago no existe",
			)

		canal_existente = await db.execute(
			select(CanalesPagos.Id).where(
				CanalesPagos.Id != canal_pago_id,
				func.lower(CanalesPagos.NombreCanal) == func.lower(nombre_canal),
			)
		)
		if canal_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe otro canal de pago con el nombre {nombre_canal}",
			)

		canal_pago.NombreCanal = nombre_canal
		await db.commit()
		await db.refresh(canal_pago)
		return RespuestaFuncion(data_registro=canal_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def _obtener_canal_pago(db: AsyncSession, canal_pago_id: int):
	resultado = await db.execute(
		select(CanalesPagos).where(CanalesPagos.Id == canal_pago_id)
	)
	return resultado.scalars().first()
