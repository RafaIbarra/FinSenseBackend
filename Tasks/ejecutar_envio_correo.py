import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Config.settings import AsyncSessionLocal
from Repositories.envio_correo_repo import obtener_envios_pendientes, procesar_envio_correo


async def ejecutar_envios_pendientes():
    print("\n=== INICIO DEL PROCESO DE ENVÍO DE CORREOS ===")

    async with AsyncSessionLocal() as db:
        print(" --> 1. Obteniendo correos pendientes")
        respuesta = await obtener_envios_pendientes(db)

        if not respuesta.success_registro:
            print(f"❌ Error al obtener correos pendientes: {respuesta.mensaje}")
            return respuesta

        envios = respuesta.data_registro or []
        print(f" --> Correos pendientes encontrados: {len(envios)}")

        for index, envio in enumerate(envios, start=1):
            print(f" --> 2. Procesando correo {index}/{len(envios)} - Id: {envio.Id}")
            resultado = await procesar_envio_correo(db, envio.Id)

            if not resultado.success_registro:
                print(f"❌ Error al procesar correo {envio.Id}: {resultado.mensaje}")
            else:
                print(f"✅ Correo {envio.Id} procesado correctamente")

            if index < len(envios):
                print(" --> Esperando 2 minutos antes del siguiente correo para evitar spam...")
                await asyncio.sleep(120)

    print("\n=== FIN DEL PROCESO DE ENVÍO DE CORREOS ===")
    return {"procesados": len(envios) if 'envios' in locals() else 0}


if __name__ == "__main__":
    import asyncio

    asyncio.run(ejecutar_envios_pendientes())
