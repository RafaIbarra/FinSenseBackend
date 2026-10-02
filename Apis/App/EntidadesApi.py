from fastapi import Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

# from Common.routers_factory import generar_router
from .router_app import generar_router_app_privada
from Config.settings import get_db
from Repositories.entidades_usuario_repo import (
	activar_entidad_usuario,
	crear_entidad_usuario,
	desactivar_entidad_usuario,
	editar_entidad_usuario,
	listar_entidades_usuario,
)
from Schemas.ApisResponseSchemas.entidades_usuarios_response_schema import EntidadesUsuariosResponse

router_entidades = generar_router_app_privada('entidades')


@router_entidades.get("/listar", response_model=list[EntidadesUsuariosResponse])
async def listar(
	request: Request,
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await listar_entidades_usuario(db, id_usuario)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return resultado.data_registro
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al listar las entidades: {str(error)}",
		)


@router_entidades.post("/registro")
async def registro_entidad(
	request: Request,
	nombre: str = Form(...),
	id: int = Form(0),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		if id > 0:
			resultado = await editar_entidad_usuario(db, id_usuario, id, nombre)
		else:
			resultado = await crear_entidad_usuario(db, id_usuario, nombre)

		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su entidad fue procesada"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al registrar la entidad: {str(error)}",
		)


@router_entidades.post("/activar")
async def activar(
	request: Request,
	id: int = Form(...),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await activar_entidad_usuario(db, id_usuario, id)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su entidad fue activada"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al activar la entidad: {str(error)}",
		)


@router_entidades.post("/desactivar")
async def desactivar(
	request: Request,
	id: int = Form(...),
	db: AsyncSession = Depends(get_db),
):
	try:
		id_usuario = int(request.state.id_usuario)
		resultado = await desactivar_entidad_usuario(db, id_usuario, id)
		if not resultado.success_registro:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado.mensaje)
		return {"detail": "Su entidad fue desactivada"}
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al desactivar la entidad: {str(error)}",
		)
