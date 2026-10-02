from fastapi import Depends, Form, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from .router_app import generar_router_app_privada
from Config.settings import get_db
from Utils.formateo_fechas import formatear_fecha_larga
from Repositories.medios_pagos_usuario_repo import (
	activar_medio_pago_usuario,
	crear_medio_pago_usuario,
	desactivar_medio_pago_usuario,
	editar_medio_pago_usuario,
	listar_medios_pagos_usuario,
)

router_medios_pagos_usuarios = generar_router_app_privada('medios-pagos-usuarios')


@router_medios_pagos_usuarios.get("/listar")
async def listar(
	request: Request,
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await listar_medios_pagos_usuario(db, id_usuario)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)

		return [
			{
				"Id": medio.Id,
				"TipoMedioPago": {
					"Id": medio.tipo_medio_pago.Id,
					"NombreTipo": medio.tipo_medio_pago.NombreTipo,
				},
				"EntidadUsuario": (
					{
						"Id": medio.entidad_usuario.Id,
						"NombreEntidad": medio.entidad_usuario.NombreEntidad,
					}
					if medio.entidad_usuario
					else None
				),
				"MarcaTarjeta": (
					{
						"Id": medio.marca_tarjeta.Id,
						"NombreMarca": medio.marca_tarjeta.NombreMarca,
					}
					if medio.marca_tarjeta
					else None
				),
				"FechaRegistro": formatear_fecha_larga(medio.FechaRegistro),
				"IsActive": medio.IsActive,
			}
			for medio in resultado.data_registro
		]
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al listar los medios de pago: {str(error)}",
		)


@router_medios_pagos_usuarios.post("/registro")
async def registro(
	request: Request,
	tipo_medio_pago_id: int = Form(...),
	entidad_usuario_id: int | None = Form(None),
	marca_tarjeta_id: int | None = Form(None),
	medio_pago_usuario_id: int = Form(0),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		if medio_pago_usuario_id > 0:
			resultado = await editar_medio_pago_usuario(
				db,
				id_usuario,
				medio_pago_usuario_id,
				tipo_medio_pago_id,
				entidad_usuario_id,
				marca_tarjeta_id,
			)
		else:
			resultado = await crear_medio_pago_usuario(
				db,
				id_usuario,
				tipo_medio_pago_id,
				entidad_usuario_id,
				marca_tarjeta_id,
			)

		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su medio de pago fue procesado"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al registrar el medio de pago: {str(error)}",
		)


@router_medios_pagos_usuarios.post("/activar")
async def activar(
	request: Request,
	id: int = Form(...),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await activar_medio_pago_usuario(db, id_usuario, id)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su medio de pago fue activado"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al activar el medio de pago: {str(error)}",
		)


@router_medios_pagos_usuarios.post("/desactivar")
async def desactivar(
	request: Request,
	id: int = Form(...),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await desactivar_medio_pago_usuario(db, id_usuario, id)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su medio de pago fue desactivado"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al desactivar el medio de pago: {str(error)}",
		)