from sqlalchemy.ext.asyncio import AsyncSession
from Repositories.canales_pagos_repo import listar_canales_pagos 
from Repositories.tipos_medios_pagos_repo import listar_tipos_medios_pagos
from Repositories.empresas_repo import listar_empresas
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd
async def obtener_catalogos_base(db: AsyncSession):
    try:
        qs_canales = await listar_canales_pagos(db)
        qs_tipos_medios = await listar_tipos_medios_pagos(db)
        qs_empresas = await listar_empresas(db)

        for respuesta in (qs_canales, qs_tipos_medios, qs_empresas):
            if not respuesta.success_registro:
                return respuesta

        data = {
            "Canales":qs_canales.data_registro,
            "TiposMedios":qs_tipos_medios.data_registro,
            "Empresas":qs_empresas.data_registro
        }
        
        return RespuestaFuncion(data_registro=data)
    except Exception as exc:
        return RespuestaFuncion(
            success_registro=False,
            mensaje=limpiar_mensaje_error_bd(str(exc)),
        )