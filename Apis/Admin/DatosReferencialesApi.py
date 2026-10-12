from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from Config.settings import get_db

from .router_admin import generar_router_admin
from Repositories.canales_pagos_repo import listar_canales_pagos 
from Repositories.tipos_medios_pagos_repo import listar_tipos_medios_pagos
from Repositories.empresas_repo import listar_empresas

router_referenciales = generar_router_admin('data-referenciales')







@router_referenciales.get("/lista-referenciales")
async def listar_canales(db: AsyncSession = Depends(get_db)):
    try:
        qs_canales = await listar_canales_pagos(db)
        qs_tipos_medios = await listar_tipos_medios_pagos(db)
        qs_empresas = await listar_empresas(db)

        valores={
            "Canales":qs_canales.data_registro,
            "TipoMedios":qs_tipos_medios.data_registro,
            "Empreas":qs_empresas.data_registro
        }

        return valores
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al listar los canales de pago: {str(error)}",
        )