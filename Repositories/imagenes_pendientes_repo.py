
from sqlalchemy.ext.asyncio import AsyncSession
from typing import  List,Tuple
from Models.ImagenesPendientes import ImagenesPendientes

from Integrations.r2_storage import *
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd
from Utils.img_works import registrar_lista_imagenes





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
        
        data_img=await registrar_lista_imagenes(imagenes=imagenes_para_subir,temp_url=False)
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




  