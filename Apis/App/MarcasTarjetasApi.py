from fastapi import Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

# from Common.routers_factory import generar_router
from .router_app import generar_router_app_privada
from Config.settings import get_db
from Repositories.marcas_tarjetas_repo import (
	activar_marca_tarjeta,
	crear_marca_tarjeta,
	desactivar_marca_tarjeta,
	editar_marca_tarjeta,
	listar_marcas_tarjetas,
)
from Schemas.ApisResponseSchemas.marcas_tarjetas_usuarios_response_schema import MarcasTarjetasUsuariosResponse

router_marcas = generar_router_app_privada('marcas')


@router_marcas.get("/listar", response_model=list[MarcasTarjetasUsuariosResponse])
async def listar(
	request: Request,
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await listar_marcas_tarjetas(db, id_usuario)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return resultado.data_registro
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al listar las marcas: {str(error)}",
		)


@router_marcas.post("/registro")
async def registro_marca(
	request: Request,
	nombre: str = Form(...),
	id: int = Form(0),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		if id > 0:
			resultado = await editar_marca_tarjeta(db, id_usuario, id, nombre)
		else:
			resultado = await crear_marca_tarjeta(db, id_usuario, nombre)

		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su marca fue procesada"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al registrar la marca: {str(error)}",
		)


@router_marcas.post("/activar")
async def activar(
	request: Request,
	id: int = Form(...),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await activar_marca_tarjeta(db, id_usuario, id)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su marca fue activada"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al activar la marca: {str(error)}",
		)


@router_marcas.post("/desactivar")
async def desactivar(
	request: Request,
	id: int = Form(...),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await desactivar_marca_tarjeta(db, id_usuario, id)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su marca fue desactivada"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al desactivar la marca: {str(error)}",
		)