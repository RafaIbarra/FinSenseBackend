from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from Integrations.r2_storage import r2_storage
from Models.ImagenesReportadas import ImagenesReportadas
from Repositories.urls_imagenes_temporales_repo import procesar_urls_temporales
from Schemas.apis_schemas import RegistroMovimientoGastoRequest
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


async def registro_reporte_imagen(
	db: AsyncSession,
	id_usuario: int,
	valores: RegistroMovimientoGastoRequest,
	observacion: str | None = None,
):
	urls_registradas = []
	urls_temporales = []

	try:
		if not id_usuario:
			return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

		if not valores:
			return RespuestaFuncion(success_registro=False, mensaje="Los datos del reporte son obligatorios")

		type_url_valor = getattr(valores.imagenes.tipo_url, "value", valores.imagenes.tipo_url)
		imagenes = valores.imagenes.urls_img
		if not imagenes:
			return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una imagen")

		imagenes = imagenes if isinstance(imagenes, list) else [imagenes]
		timestamp = datetime.now().strftime("%Y_%m_%d_T_%H_%M_%S")
		codigo_reporte = f"U_{id_usuario}_R_{timestamp}"

		for url_temporal in imagenes[:2]:
			if type_url_valor != "Temporal":
				urls_registradas.append(url_temporal)
				continue

			resultado = r2_storage.move_between_buckets(
				source_url=url_temporal,
				source_bucket=r2_storage.bucket_temporales,
				dest_bucket=r2_storage.bucket_gastos,
			)
			if not resultado.get("success"):
				raise RuntimeError(
					resultado.get("message", "No se pudo mover la imagen temporal")
				)

			urls_registradas.append(resultado.get("url"))
			urls_temporales.append(url_temporal)

		for url in urls_registradas:
			if not url:
				continue

			db.add(
				ImagenesReportadas(
					CodigoReporte=codigo_reporte,
					UrlImagen=url,
					UsuarioId=id_usuario,
					ResultadoExtraccion=valores.factura.model_dump(),
					ResultadoClasificacion=valores.clasificacion.model_dump(),
					Observacion=observacion,
				)
			)

		if urls_temporales:
			resultado_procesamiento = await procesar_urls_temporales(
				db,
				id_usuario,
				urls_temporales,
			)
			if not resultado_procesamiento.success:
				raise RuntimeError(resultado_procesamiento.mensaje or "No se pudieron procesar las URLs temporales")

		await db.commit()
		return RespuestaFuncion()
	except Exception as exc:
		await db.rollback()

		for url in urls_registradas:
			try:
				if type_url_valor == "Temporal":
					r2_storage.delete_gasto_image(url)
			except Exception:
				pass

		return RespuestaFuncion(
			success_registro=False,
			mensaje=limpiar_mensaje_error_bd(str(exc)),
		)
