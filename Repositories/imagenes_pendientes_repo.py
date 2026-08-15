from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.ImagenesPendientes import ImagenesPendientes
from Utils.img_works import registrar_imagenes
from Integrations.r2_storage import *
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import *
async def registrar_imagenes_pendientes(db: AsyncSession, codigo_tarea: str, id_usuario: int, imagenes, motivo: str):
    """Recibe imágenes, las sube a R2 y registra sus URLs pendientes para una tarea y usuario."""
    imagenes_subidas = []
    try:
        if not codigo_tarea:
            return RespuestaFuncion(success_registro=False, mensaje="El código de tarea es obligatorio")

        if not id_usuario:
            return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

        if not imagenes:
            return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una imagen")

        imagenes = imagenes if isinstance(imagenes, list) else [imagenes]

        registros = []
        imagenes_errores = []
        mensaje_imagen=""
        # --- Paso 1: subir imágenes a R2 ---
        for index, img in enumerate(imagenes[:2], start=1):
            try:
                resultado = await registrar_imagenes(img, {"index": index})
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

        # Si alguna imagen falló al subirse, se eliminan las que sí se subieron
        if imagenes_errores:
            for ur in imagenes_subidas:
                try:
                    r2_storage.delete_gasto_image(ur)
                except Exception:
                    pass
            return RespuestaFuncion(success_registro=False, mensaje=mensaje_imagen)

        # --- Paso 2: registrar todas en la BD (todo o nada) ---
        try:
            for ur in imagenes_subidas:
                registro = ImagenesPendientes(
                    CodigoTarea=codigo_tarea,
                    UrlImagen=ur,
                    UsuarioId=id_usuario,
                    Motivo=motivo,
                )
                db.add(registro)
                registros.append(registro)

            await db.commit()

        except Exception as e:
            # Si algo falló al registrar, se revierte la BD y se borran todas las imágenes de R2
            await db.rollback()
            for ur in imagenes_subidas:
                try:
                    r2_storage.delete_gasto_image(ur)
                except Exception:
                    pass
            error_bd=limpiar_mensaje_error_bd(str(e))
            msj=f"No se pudieron registrar las imágenes, se revirtieron los cambios; {error_bd}"
            return RespuestaFuncion(success_registro=False, mensaje=msj)

        for registro in registros:
            await db.refresh(registro)

        return RespuestaFuncion()

    except Exception as e:
        await db.rollback()
        # Por seguridad, si algo se subió pero no se llegó a limpiar, se limpia aquí también
        for ur in imagenes_subidas:
            try:
                r2_storage.delete_gasto_image(ur)
            except Exception:
                pass
        return RespuestaFuncion(success_registro=False, mensaje=str(e))