from sqlalchemy.ext.asyncio import AsyncSession
from Config.settings import AsyncSessionLocal
from Models.ErroresModelos import ErroresModelos
from Schemas.Respuestas import RespuestaFuncion


async def registro_error(error_data: dict):
    async with AsyncSessionLocal() as db:
        try:
            nuevo_error = ErroresModelos(
                Proceso=error_data.get("proceso", ""),
                NombreModelo=error_data.get("modelo", ""),
                RespuestaError=error_data.get("respuesta", ""),
            )

            db.add(nuevo_error)
            await db.commit()
            await db.refresh(nuevo_error)

            return RespuestaFuncion()

        except Exception as error:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=str(error),
            )