import sys
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from Config.settings import AsyncSessionLocal,settings
from Models.UrlsImagenesTemporales import UrlsImagenesTemporales
from Repositories.envio_correo_repo import registro_envio_correo

from Integrations.r2_storage import r2_storage

from Utils.error_utils import limpiar_mensaje_error_bd
async def registros_pendientes(db):
    fecha_limite = datetime.now(timezone.utc) - timedelta(minutes=settings.URLS_TEMPORALES_MINUTOS)
    print(f" --> 1. Buscando URLs pendientes anteriores a {fecha_limite.isoformat()}")
    resultado = await db.execute(
        select(UrlsImagenesTemporales)
        .where(
            UrlsImagenesTemporales.PendienteEliminacion.is_(True),
            UrlsImagenesTemporales.FechaRegistro < fecha_limite,
        )
        .options(selectinload(UrlsImagenesTemporales.usuario))
        .order_by(UrlsImagenesTemporales.FechaRegistro.asc())
    )
    registros = resultado.scalars().all()
    print(f" --> URLs pendientes encontradas: {len(registros)}")
    return registros

async def registrar_correo_resumen_eliminados(db, resumen: list):
    if not resumen:
        return

    correo = {
        "destinatario": settings.MAIL_ADMIN,
        "asunto": "URLS TEMPORALES ELIMINADAS",
        "nombre_template": "urls_temp_eliminadas.html",
        "data": resumen,
        "context_key": "resumen",
        "usuario_id": None,
    }

    respuesta = await registro_envio_correo(db, correo)
    if respuesta.success_registro:
        print(f"[NOTIFICACION] Correo registrado para {settings.MAIL_ADMIN}.")
    else:
        print(f"[NOTIFICACION] No se pudo registrar correo para {settings.MAIL_ADMIN}: {respuesta.mensaje}")

   
        

async def delete_img():
    print("\n=== INICIO DEL PROCESO DE ELIMINACION ===")
    async with AsyncSessionLocal() as db:
        registros = await registros_pendientes(db)
        eliminadas = 0
        resumen = []

        for numero, registro in enumerate(registros, start=1):
            print(f" ✅. Eliminando imagen {numero}/{len(registros)}: {registro.UrlImagen}")
            resultado = r2_storage.delete_temp_image(registro.UrlImagen)
            if not resultado.get("success", False):
                print(f" ❌ Error eliminando URL temporal: {resultado}")
                continue

            print(" ✅. Actualizando registro en la base de datos")
            fecha_eliminacion = datetime.now(timezone.utc)
            try:
                await db.execute(
                    update(UrlsImagenesTemporales)
                    .where(UrlsImagenesTemporales.Id == registro.Id)
                    .values(
                        FechaEliminacion=fecha_eliminacion,
                        PendienteEliminacion=False,
                    )
                )
                eliminadas += 1
                resumen.append(
                    {
                        "Nombre y Apellido Usuario": (
                            f"{registro.usuario.NombreUsuario} {registro.usuario.ApellidoUsuario}"
                        ),
                        "Url": registro.UrlImagen,
                        "FechaRegistro": registro.FechaRegistro.strftime("%d/%m/%y %H:%M:%S"),
                        "FechaEliminacion": fecha_eliminacion.strftime("%d/%m/%y %H:%M:%S"),
                    }
                )
            except Exception as exc:
                    await db.rollback()
                    print(f"❌ Error en actualizacion {registro.Id}: {limpiar_mensaje_error_bd(exc)}")
                    continue
            print(" ##############################################//##############################################")
            


        print(" --> 3. Confirmando cambios en la base de datos")
        await db.commit()
        if resumen:
            print(" --> 4. Envio de notificacion")
            await registrar_correo_resumen_eliminados(db, resumen)
        print(f"URLs temporales procesadas: {len(registros)}")
        print(f"URLs temporales eliminadas: {eliminadas}")
        

        print("\n=== FIN DEL PROCESO ===")
        return resumen


if __name__ == "__main__":
    import asyncio

    asyncio.run(delete_img())
