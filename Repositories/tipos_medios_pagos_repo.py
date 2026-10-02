from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.TiposMediosPagos import TiposMediosPagos
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def listar_tipos_medios_pagos(db: AsyncSession):
	try:
		resultado = await db.execute(
			select(TiposMediosPagos).order_by(TiposMediosPagos.Id.desc())
		)
		return RespuestaFuncion(data_registro=resultado.scalars().all())
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def crear_tipo_medio_pago(
	db: AsyncSession,
	nombre_tipo: str,
	es_debito: bool = True,
	solicitar_marca: bool = True,
	solicitar_entidad: bool = True,
):
	nombre_tipo = str(nombre_tipo or "").strip()
	if not nombre_tipo:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre del tipo de medio de pago es obligatorio",
		)

	try:
		tipo_existente = await db.execute(
			select(TiposMediosPagos.Id).where(
				func.lower(TiposMediosPagos.NombreTipo) == func.lower(nombre_tipo),
			)
		)
		if tipo_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe un tipo de medio de pago con el nombre {nombre_tipo}",
			)

		tipo_medio_pago = TiposMediosPagos(
			NombreTipo=nombre_tipo,
			EsDebito=es_debito,
			SolicitarMarca=solicitar_marca,
			SolicitarEntidad=solicitar_entidad,
		)
		db.add(tipo_medio_pago)
		await db.commit()
		await db.refresh(tipo_medio_pago)
		return RespuestaFuncion(data_registro=tipo_medio_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def editar_tipo_medio_pago(
	db: AsyncSession,
	tipo_medio_pago_id: int,
	nombre_tipo: str,
	es_debito: bool = True,
	solicitar_marca: bool = True,
	solicitar_entidad: bool = True,
):
	nombre_tipo = str(nombre_tipo or "").strip()
	if tipo_medio_pago_id <= 0:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El tipo de medio de pago es obligatorio",
		)
	if not nombre_tipo:
		return RespuestaFuncion(
			success_registro=False,
			mensaje="El nombre del tipo de medio de pago es obligatorio",
		)

	try:
		tipo_medio_pago = await _obtener_tipo_medio_pago(db, tipo_medio_pago_id)
		if not tipo_medio_pago:
			return RespuestaFuncion(
				success_registro=False,
				mensaje="El tipo de medio de pago no existe",
			)

		tipo_existente = await db.execute(
			select(TiposMediosPagos.Id).where(
				TiposMediosPagos.Id != tipo_medio_pago_id,
				func.lower(TiposMediosPagos.NombreTipo) == func.lower(nombre_tipo),
			)
		)
		if tipo_existente.scalar_one_or_none() is not None:
			return RespuestaFuncion(
				success_registro=False,
				mensaje=f"Ya existe otro tipo de medio de pago con el nombre {nombre_tipo}",
			)

		tipo_medio_pago.NombreTipo = nombre_tipo
		tipo_medio_pago.EsDebito = es_debito
		tipo_medio_pago.SolicitarMarca = solicitar_marca
		tipo_medio_pago.SolicitarEntidad = solicitar_entidad
		await db.commit()
		await db.refresh(tipo_medio_pago)
		return RespuestaFuncion(data_registro=tipo_medio_pago)
	except Exception as error:
		await db.rollback()
		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(error)),
		)


async def _obtener_tipo_medio_pago(db: AsyncSession, tipo_medio_pago_id: int):
	resultado = await db.execute(
		select(TiposMediosPagos).where(TiposMediosPagos.Id == tipo_medio_pago_id)
	)
	return resultado.scalars().first()
