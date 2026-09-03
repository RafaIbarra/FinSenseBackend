
from typing import List, Union, Tuple
from Integrations.r2_storage import r2_storage
from Schemas.r2_storage_schemas import RespuestaImagenesSubidas, TipoUrlEnum


async def registrar_lista_imagenes(
    imagenes: Union[List[Tuple[bytes, str]], Tuple[bytes, str]],
    temp_url: bool,
) -> RespuestaImagenesSubidas:
    """
    Sube hasta 2 imágenes a R2.
    Si procesar=True  -> sube al bucket de gastos (Procesada).
    Si procesar=False -> sube al bucket de escaneadas (Escaneada).
    Si alguna falla, hace rollback eliminando las ya subidas.
    """
    if not isinstance(imagenes, list):
        imagenes = [imagenes]

    imagenes_errores: List[int] = []
    imagenes_subidas: List[str] = []
    mensaje_error = ""
    registro_correcto = True

    for index, item in enumerate(imagenes[:2], start=1):
        try:
            # Soporta tanto (bytes, str) como (bytes, mime, str)
            if len(item) == 3:
                file_bytes, _, file_name = item
            else:
                file_bytes, file_name = item

            resultado = await registrar_imagen(file_bytes, file_name, temp_url)

            if resultado.get("success") and resultado.get("url"):
                imagenes_subidas.append(resultado["url"])
            else:
                imagenes_errores.append(index)
                mensaje_error = resultado.get("mensaje", "Error desconocido al subir imagen")
        except Exception as exc:
            imagenes_errores.append(index)
            mensaje_error = str(exc)
            continue

    # Rollback: si hubo errores, eliminar las imágenes ya subidas
    if imagenes_errores and imagenes_subidas:
        for url in imagenes_subidas:
            try:
                if not temp_url:
                    r2_storage.delete_gasto_image(url)
                else:
                    r2_storage.delete_temp_image(url)
            except Exception:
                pass
        registro_correcto = False
        imagenes_subidas = []

    return RespuestaImagenesSubidas(
        urls_img=imagenes_subidas,
        success=registro_correcto,
        mensaje_error_subida=mensaje_error,
        tipo_url=TipoUrlEnum.Temporal if temp_url else TipoUrlEnum.Procesada,
    )


async def registrar_imagen(
    file_bytes: bytes,
    file_name: str,
    temp_url: bool,
):
    """
    Sube una imagen a R2.
    Si procesar=True  -> upload_gasto_image.
    Si procesar=False -> upload_escaneada_image.
    """
    try:
        if not file_bytes:
            return {"url": None, "mensaje": "La imagen viene vacía.", "success": False}

        if not temp_url:
            resultado = r2_storage.upload_gasto_image(
                file_bytes=file_bytes,
                file_name=file_name,
            )
        else:
            resultado = r2_storage.upload_temp_image(
                file_bytes=file_bytes,
                file_name=file_name,
            )

        url_imagen = resultado.get("url")
        success = resultado.get("success", False)

        if not success or not url_imagen:
            return {
                "url": None,
                "mensaje": resultado.get("message") or "No se obtuvo la URL de la imagen subida.",
                "success": False,
            }

        return {
            "url": url_imagen,
            "mensaje": "",
            "success": True,
        }

    except Exception as exc:
        return {
            "url": None,
            "mensaje": str(exc),
            "success": False,
        }