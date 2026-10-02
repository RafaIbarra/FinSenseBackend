import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from Config.settings import AsyncSessionLocal, async_engine
from Models.TiposMediosPagos import TiposMediosPagos


TIPOS_MEDIOS_PAGOS = (
	("Tarjeta Credito", False, True, True),
	("Tarjeta Debito", True, True, True),
	("Efectivo", True, False, False),
	("Caja Ahorro", True, False, True),
)


async def crear_tipos_medios_pagos():
	nombres = [nombre for nombre, _, _, _ in TIPOS_MEDIOS_PAGOS]

	async with AsyncSessionLocal() as db:
		resultado = await db.execute(
			select(TiposMediosPagos).where(
				TiposMediosPagos.NombreTipo.in_(nombres)
			)
		)
		tipos_existentes = {
			tipo.NombreTipo: tipo for tipo in resultado.scalars().all()
		}

		tipos_nuevos = [
			TiposMediosPagos(
				NombreTipo=nombre,
				EsDebito=es_debito,
				SolicitarMarca=solicitar_marca,
				SolicitarEntidad=solicitar_entidad,
			)
			for nombre, es_debito, solicitar_marca, solicitar_entidad in TIPOS_MEDIOS_PAGOS
			if nombre not in tipos_existentes
		]
		efectivo = tipos_existentes.get("Efectivo")
		efectivo_actualizado = False
		if efectivo:
			efectivo_actualizado = (
				efectivo.SolicitarMarca is not False
				or efectivo.SolicitarEntidad is not False
			)
			efectivo.SolicitarMarca = False
			efectivo.SolicitarEntidad = False

		if tipos_nuevos:
			db.add_all(tipos_nuevos)
		if tipos_nuevos or efectivo_actualizado:
			await db.commit()

		print(f"Tipos de medios de pago creados: {len(tipos_nuevos)}")
		print(f"Tipos que ya existían: {len(TIPOS_MEDIOS_PAGOS) - len(tipos_nuevos)}")
		print(f"Efectivo actualizado: {'Sí' if efectivo_actualizado else 'No'}")


async def main():
	try:
		await crear_tipos_medios_pagos()
	finally:
		await async_engine.dispose()


if __name__ == "__main__":
	asyncio.run(main())
