import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from Config.settings import AsyncSessionLocal, async_engine
from Models.CanalesPagos import CanalesPagos


NOMBRES_CANALES = ("QR", "Transferencias", "Pos")


async def crear_canales():
	async with AsyncSessionLocal() as db:
		resultado = await db.execute(
			select(CanalesPagos.NombreCanal).where(
				CanalesPagos.NombreCanal.in_(NOMBRES_CANALES)
			)
		)
		nombres_existentes = set(resultado.scalars().all())

		canales_nuevos = [
			CanalesPagos(NombreCanal=nombre)
			for nombre in NOMBRES_CANALES
			if nombre not in nombres_existentes
		]

		if canales_nuevos:
			db.add_all(canales_nuevos)
			await db.commit()

		print(f"Canales creados: {len(canales_nuevos)}")
		print(f"Canales omitidos por existir: {len(NOMBRES_CANALES) - len(canales_nuevos)}")


async def main():
	try:
		await crear_canales()
	finally:
		await async_engine.dispose()


if __name__ == "__main__":
	asyncio.run(main())
