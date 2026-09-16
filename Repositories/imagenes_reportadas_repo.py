from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Integrations.r2_storage import r2_storage
from Models.ImagenesReportadas import ImagenesReportadas
from Models.ImagenesReportadasUrls import ImagenesReportadasUrls
from Models.Usuarios import Usuarios
from Repositories.urls_imagenes_temporales_repo import procesar_urls_temporales
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd


def _extraer_url(item: Any) -> str | None:
	"""Normaliza un elemento de 'urls_img', que puede venir como:
	- string plano: "https://..."
	- dict: {"url": "https://...", "size_bytes": 12345}
	Devuelve el string de la url o None si no se pudo extraer.
	"""
	if isinstance(item, Mapping):
		url = item.get("url")
		return url if isinstance(url, str) else None
	if isinstance(item, str):
		return item
	return None


async def registro_reporte_imagen(
	db: AsyncSession,
	id_usuario: int,
	valores: dict[str, Any],
):
	urls_registradas = []
	urls_temporales = []

	try:
		if not id_usuario:
			return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

		if not isinstance(valores, Mapping):
			return RespuestaFuncion(success_registro=False, mensaje="Los datos del reporte son obligatorios")
		
		respuesta = dict(valores)
		detail = respuesta.get("detail")
		if not isinstance(detail, Mapping):
			detail = {}

		imagenes_data = respuesta.get("imagenes", detail.get("imagenes"))
		if isinstance(imagenes_data, Mapping):
			type_url_valor = imagenes_data.get("tipo_url")
			imagenes = imagenes_data.get("urls_img")
		else:
			type_url_valor = None
			imagenes = imagenes_data

		print(f'imagenes_data : {imagenes_data}')

		if hasattr(type_url_valor, "value"):
			print('aca ahce')
			type_url_valor = type_url_valor.value
		observacion = respuesta.get("observacion", detail.get("observacion"))
		if not imagenes:
			return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una imagen")

		imagenes = imagenes if isinstance(imagenes, list) else [imagenes]
		imagenes = [_extraer_url(item) for item in imagenes]
		imagenes = [url for url in imagenes if url]

		if not imagenes:
			return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una imagen valida")

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

		reporte = ImagenesReportadas(
			UsuarioId=id_usuario,
			Respuesta=respuesta,
			Observacion=observacion,
		)
		reporte.urls = [
			ImagenesReportadasUrls(
				UrlImagen=url,
			)
			for url in urls_registradas
			if url
		]
		db.add(reporte)

		if urls_temporales:
			resultado_procesamiento = await procesar_urls_temporales(
				db,
				id_usuario,
				urls_temporales,
			)
			if not resultado_procesamiento.success_registro:
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


async def listado_reportados(db: AsyncSession):
	try:
		result = await db.execute(
			select(
				ImagenesReportadas,
				ImagenesReportadasUrls,
				Usuarios.Id,
				Usuarios.NombreUsuario,
				Usuarios.ApellidoUsuario,
				Usuarios.UserName,
			)
			.join(ImagenesReportadasUrls, ImagenesReportadasUrls.ImagenesReportadasId == ImagenesReportadas.Id)
			.outerjoin(Usuarios, ImagenesReportadas.UsuarioId == Usuarios.Id)
			.order_by(ImagenesReportadas.FechaRegistro.desc())
		)

		registros = [
			{
				"id": reporte.Id,
				"url_imagen": url_reporte.UrlImagen,
				"fecha_registro": reporte.FechaRegistro,
				"usuario_id": reporte.UsuarioId,
				"respuesta": reporte.Respuesta,
				"observacion": reporte.Observacion,
				"estado_resolucion": reporte.EstadoResolucion,
				"resolucion": reporte.Resolucion,
				"fecha_resolucion": reporte.FechaResolucion,
				"id_usuario": id_usuario,
				"nombre_usuario": nombre_usuario,
				"apellido_usuario": apellido_usuario,
				"user_name": user_name,
			}
			for reporte, url_reporte, id_usuario, nombre_usuario, apellido_usuario, user_name in result.all()
		]
		return RespuestaFuncion(data_registro=registros)
	except Exception as e:
		await db.rollback()
		return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))