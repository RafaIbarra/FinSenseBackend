from Integrations.r2_storage import *
from Schemas.Respuestas import RespuestaImagenesSubidas


async def registrar_lista_imagenes(imagenes):
    imagenes = imagenes if isinstance(imagenes, list) else [imagenes]
    
    imagenes_errores = []
    mensaje_imagen=""
    imagenes_subidas = []
    listado_urls=[]
    registro_correcto=True
    for index, (file_bytes, file_name) in enumerate(imagenes[:2], start=1):
        try:
            resultado = await registrar_imagenes(file_bytes, file_name)
            url_imagen = resultado.get("url")
            success_imagen = resultado.get("success", False)
            mensaje_imagen=resultado.get("mensaje", False)
            if success_imagen:
                imagenes_subidas.append(url_imagen)
            else:
                imagenes_errores.append(index)
        except Exception:
            imagenes_errores.append(index)
            continue
    if imagenes_errores:
        registro_correcto=False
        for ur in imagenes_subidas:
            try:
                r2_storage.delete_gasto_image(ur)
            except Exception:
                pass
    else:
        listado_urls=imagenes_subidas.copy()
    return RespuestaImagenesSubidas(urls_img=listado_urls,success=registro_correcto,mensaje_error=mensaje_imagen)
    


async def registrar_imagenes(file_bytes: bytes, file_name: str):
    """Sube una imagen a R2 y devuelve url + mensaje de error si aplica."""
    try:
        if not file_bytes:
            return {"url": None, "mensaje": "La imagen viene vacía."}
        

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

