from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .router_app import generar_router_app_privada
from Config.settings import get_db
from Repositories.canales_pagos_repo import (
	listar_canales_pagos as obtener_canales_pagos,
)
from Repositories.tipos_medios_pagos_repo import (
	listar_tipos_medios_pagos as obtener_tipos_medios_pagos,
)

router_catalogo = generar_router_app_privada('catalog-medio-pago')


@router_catalogo.get("/lista-canales")
async def listar_canales(db: AsyncSession = Depends(get_db)):
	try:
		resultado = await obtener_canales_pagos(db)
		if not resultado.success_registro:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=resultado.mensaje,
			)
		return resultado.data_registro
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al listar los canales de pago: {str(error)}",
		)


@router_catalogo.get("/lista-tipo-medio")
async def listar_tipos(db: AsyncSession = Depends(get_db)):
	try:
		resultado = await obtener_tipos_medios_pagos(db)
		if not resultado.success_registro:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=resultado.mensaje,
			)
		return resultado.data_registro
	except HTTPException:
		raise
	except Exception as error:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"Error al listar los tipos de medios de pago: {str(error)}",
		)