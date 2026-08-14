from Integrations.r2_storage import *


async def registrar_imagenes(img, contexto):
    """Sube una imagen a R2 y devuelve url + mensaje de error si aplica."""
    try:
        if hasattr(img, "read") and callable(img.read):
            try:
                await img.seek(0)
            except Exception:
                pass
            file_bytes = await img.read()
            file_name = getattr(img, "filename", None) or getattr(img, "name", None) or "factura.jpg"
        elif isinstance(img, (bytes, bytearray)):
            file_bytes = bytes(img)
            file_name = "factura.jpg"
        elif isinstance(img, dict):
            file_bytes = img.get("bytes") or img.get("content") or b""
            file_name = img.get("filename") or img.get("name") or "factura.jpg"
        else:
            return {
                "url": None,
                "mensaje": "No se recibió una imagen válida."
            }

        if not file_bytes:
            return {
                "url": None,
                "mensaje": "La imagen viene vacía."
            }

        resultado = r2_storage.upload_gasto_image(
            file_bytes=file_bytes,
            file_name=file_name,
        )
        
        url_imagen = resultado.get("url") or None
        success= resultado.get("success") or False
        if not resultado.get("success") or not url_imagen:
            
            return {
                "url": None,
                "mensaje": resultado.get("message") or "No se obtuvo la URL de la imagen subida.",
                'success':success
            }

        
        return {
            "url": url_imagen,
            "mensaje": "",
            'success':success
        }

    except Exception as exc:
        return {
            "url": None,
            "mensaje": str(exc)
        }

