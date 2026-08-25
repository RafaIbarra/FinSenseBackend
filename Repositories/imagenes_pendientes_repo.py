from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import  List,Tuple
from Models.ImagenesPendientes import ImagenesPendientes
from Models.MovimientosGastos import MovimientosGastos
from Models.MovimientosGastosEtiquetas import MovimientosGastosEtiquetas
from Utils.img_works import registrar_imagenes
from Integrations.r2_storage import *
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd
from Utils.img_works import registrar_lista_imagenes
from sqlalchemy.orm import selectinload




async def registrar_imagenes_pendientes(db: AsyncSession, id_usuario: int, imagenes: List[Tuple[bytes, str, str]], motivo: str):
    try:
        ts = datetime.now()
        formateado=ts.strftime("%Y_%m_%d_T_%H_%M_%S")
        codigo_tarea = f'U_{id_usuario}_F_{formateado}'
        if not codigo_tarea:
            return RespuestaFuncion(success_registro=False, mensaje="El código de tarea es obligatorio")

        if not id_usuario:
            return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

        if not imagenes:
            return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una imagen")
        imagen_1, mime_type_1, filename_1 = imagenes[0]
        imagen_2, mime_type_2, filename_2 = None, "image/jpeg", "factura.jpg"
        imagenes_para_subir = [(imagen_1, filename_1),]
        if len(imagenes) > 1:
            imagen_2, mime_type_2, filename_2 = imagenes[1]
        
        if imagen_2:
            imagenes_para_subir.append((imagen_2, filename_2))
        
        data_img=await registrar_lista_imagenes(imagenes_para_subir)
        if not data_img.success:

            return RespuestaFuncion(success_registro=False, mensaje=data_img.mensaje_error)
        
        list_urls=data_img.urls_img
        if list_urls:
            list_urls = list_urls if isinstance(list_urls, list) else [list_urls]
            for index, img in enumerate(list_urls[:2], start=1):
                try:
                    imagen = ImagenesPendientes(
                    CodigoTarea=codigo_tarea,
                        UrlImagen=img,
                        UsuarioId=id_usuario,
                        Motivo=motivo,
                    )
                    db.add(imagen)

                except Exception as exc:
                    print(f'Error procesando imagen {index}: {exc}')

            await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        
        for ur in list_urls:
            try:
                r2_storage.delete_gasto_image(ur)
            except Exception:
                pass
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))




    # """Recibe imágenes, las sube a R2 y registra sus URLs pendientes para una tarea y usuario."""
    # imagenes_subidas = []
    # try:
    #     if not codigo_tarea:
    #         return RespuestaFuncion(success_registro=False, mensaje="El código de tarea es obligatorio")

    #     if not id_usuario:
    #         return RespuestaFuncion(success_registro=False, mensaje="El usuario es obligatorio")

    #     if not imagenes:
    #         return RespuestaFuncion(success_registro=False, mensaje="Debe enviarse al menos una imagen")

    #     imagenes = imagenes if isinstance(imagenes, list) else [imagenes]

    #     registros = []
    #     imagenes_errores = []
    #     mensaje_imagen=""
    #     # --- Paso 1: subir imágenes a R2 ---
    #     for index, img in enumerate(imagenes[:2], start=1):
    #         try:
    #             resultado = await registrar_imagenes(img, {"index": index})
    #             url_imagen = resultado.get("url")
    #             success_imagen = resultado.get("success", False)
    #             mensaje_imagen=resultado.get("mensaje", False)
    #             if success_imagen:
    #                 imagenes_subidas.append(url_imagen)
    #             else:
    #                 imagenes_errores.append(index)
    #         except Exception:
    #             imagenes_errores.append(index)
    #             continue

    #     # Si alguna imagen falló al subirse, se eliminan las que sí se subieron
    #     if imagenes_errores:
    #         for ur in imagenes_subidas:
    #             try:
    #                 r2_storage.delete_gasto_image(ur)
    #             except Exception:
    #                 pass
    #         return RespuestaFuncion(success_registro=False, mensaje=mensaje_imagen)

    #     # --- Paso 2: registrar todas en la BD (todo o nada) ---
    #     try:
    #         for ur in imagenes_subidas:
    #             registro = ImagenesPendientes(
    #                 CodigoTarea=codigo_tarea,
    #                 UrlImagen=ur,
    #                 UsuarioId=id_usuario,
    #                 Motivo=motivo,
    #             )
    #             db.add(registro)
    #             registros.append(registro)

    #         await db.commit()

    #     except Exception as e:
    #         # Si algo falló al registrar, se revierte la BD y se borran todas las imágenes de R2
    #         await db.rollback()
    #         for ur in imagenes_subidas:
    #             try:
    #                 r2_storage.delete_gasto_image(ur)
    #             except Exception:
    #                 pass
    #         error_bd=limpiar_mensaje_error_bd(str(e))
    #         msj=f"No se pudieron registrar las imágenes, se revirtieron los cambios; {error_bd}"
    #         return RespuestaFuncion(success_registro=False, mensaje=msj)

    #     for registro in registros:
    #         await db.refresh(registro)

    #     return RespuestaFuncion()

    # except Exception as e:
    #     await db.rollback()
    #     # Por seguridad, si algo se subió pero no se llegó a limpiar, se limpia aquí también
    #     for ur in imagenes_subidas:
    #         try:
    #             r2_storage.delete_gasto_image(ur)
    #         except Exception:
    #             pass
    #     return RespuestaFuncion(success_registro=False, mensaje=str(e))