import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from Config.settings import AsyncSessionLocal, async_engine
from Models.Temas import Temas


ARCHIVO_COLORES = Path(__file__).resolve().parent / "colores.json"


def cargar_temas():
	with ARCHIVO_COLORES.open("r", encoding="utf-8") as archivo:
		datos = json.load(archivo)

	if not isinstance(datos, list):
		raise ValueError("colores.json debe contener una lista de temas")

	return datos


async def importar_temas():
	datos = cargar_temas()
	nombres = [tema.get("nombre") for tema in datos]

	if any(not nombre for nombre in nombres):
		raise ValueError("Cada tema debe tener un campo 'nombre' no vacío")

	async with AsyncSessionLocal() as db:
		resultado = await db.execute(
			select(Temas.NombreTema).where(Temas.NombreTema.in_(nombres))
		)
		nombres_existentes = set(resultado.scalars().all())

		temas_nuevos = [
			Temas(
				NombreTema=tema["nombre"],
				Tipo=tema.get("tipo"),
				Descripcion=tema.get("descripcion"),
			)
			for tema in datos
			if tema["nombre"] not in nombres_existentes
		]

		if temas_nuevos:
			db.add_all(temas_nuevos)
			await db.commit()

		print(f"Temas insertados: {len(temas_nuevos)}")
		print(f"Temas omitidos por existir: {len(datos) - len(temas_nuevos)}")


async def main():
	try:
		await importar_temas()
	finally:
		await async_engine.dispose()


if __name__ == "__main__":
	asyncio.run(main())
