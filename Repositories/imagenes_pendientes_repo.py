
from sqlalchemy import  select
from sqlalchemy.orm import selectinload,load_only
from sqlalchemy.ext.asyncio import AsyncSession
from typing import  List,Tuple

from Models.ImagenesPendientes import ImagenesPendientes
from Models.MovimientosGastos import MovimientosGastos
from Models.MovimientosGastosEtiquetas import MovimientosGastosEtiquetas
from Models.MediosPagosUsuarios import MediosPagosUsuarios
from Models.CanalesPagos import CanalesPagos
from Models.Usuarios import Usuarios

from Integrations.r2_storage import *
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd
from Utils.img_works import registrar_lista_imagenes
from Utils.formateo_fechas import formatear_fecha_larga

async def registrar_imagenes_pendientes(db: AsyncSession, id_usuario: int, imagenes: List[Tuple[bytes, str, str]], motivo: str,medios_pagos:list=[]):
    list_urls = []
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

        if medios_pagos:
            if not isinstance(medios_pagos, list):
                return RespuestaFuncion(
                    success_registro=False,
                    mensaje="Los medios de pago deben enviarse como una lista",
                )

            for medio_pago in medios_pagos:
                if not isinstance(medio_pago, dict):
                    return RespuestaFuncion(
                        success_registro=False,
                        mensaje="Cada medio de pago debe ser un objeto",
                    )

                id_medio = medio_pago.get("id_medio")
                if id_medio is None:
                    return RespuestaFuncion(
                        success_registro=False,
                        mensaje="Cada medio de pago debe incluir su id_medio",
                    )

                monto_medio = medio_pago.get("monto_medio")
                if monto_medio is None:
                    return RespuestaFuncion(
                        success_registro=False,
                        mensaje="Cada medio de pago debe incluir su monto_medio",
                    )
                try:
                    if monto_medio < 0:
                        return RespuestaFuncion(
                            success_registro=False,
                            mensaje="El monto de un medio de pago no puede ser negativo",
                        )
                except TypeError:
                    return RespuestaFuncion(
                        success_registro=False,
                        mensaje="El monto de un medio de pago debe ser numérico",
                    )

                medio_result = await db.execute(
                    select(MediosPagosUsuarios.Id).where(
                        MediosPagosUsuarios.Id == id_medio,
                        MediosPagosUsuarios.UsuarioId == id_usuario,
                        MediosPagosUsuarios.IsActive.is_(True),
                    )
                )
                if medio_result.scalar_one_or_none() is None:
                    return RespuestaFuncion(
                        success_registro=False,
                        mensaje=f"El medio de pago {id_medio} no existe, no pertenece al usuario o está inactivo",
                    )

                if "canal_pago_id" in medio_pago:
                    canal_result = await db.execute(
                        select(CanalesPagos.Id).where(
                            CanalesPagos.Id == medio_pago["canal_pago_id"],
                        )
                    )
                    if canal_result.scalar_one_or_none() is None:
                        return RespuestaFuncion(
                            success_registro=False,
                            mensaje=f"El canal de pago {medio_pago['canal_pago_id']} no existe",
                        )

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
                    url_imagen = img["url"] if isinstance(img, dict) else img
                    size_bytes = img.get("size_bytes", 0) if isinstance(img, dict) else 0
                    imagen = ImagenesPendientes(
                    CodigoTarea=codigo_tarea,
                        UrlImagen=url_imagen,
                        UsuarioId=id_usuario,
                        Motivo=motivo,
                        TamañoImagen=size_bytes,
                        MediosPagos=medios_pagos
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
                url_imagen = ur["url"] if isinstance(ur, dict) else ur
                r2_storage.delete_gasto_image(url_imagen)
            except Exception:
                pass
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))



async def listado_imagenes_pendientes(db: AsyncSession):
    try:
        result = await db.execute(
            select(ImagenesPendientes)
            .options(
                selectinload(ImagenesPendientes.movimiento).selectinload(
                    MovimientosGastos.categoria
                ),
                selectinload(ImagenesPendientes.movimiento).selectinload(
                    MovimientosGastos.empresa
                ),
                selectinload(ImagenesPendientes.movimiento)
                .selectinload(MovimientosGastos.etiquetas)
                .selectinload(MovimientosGastosEtiquetas.etiqueta),
            )
            .order_by(ImagenesPendientes.FechaRegistro.desc())
        )
        imagenes = result.scalars().all()

        

        respuesta= [
            {
                "id": imagen.Id,
                "codigo_tarea": imagen.CodigoTarea,
                "url_imagen": imagen.UrlImagen,
                "fecha_registro": formatear_fecha_larga(imagen.FechaRegistro),
                "motivo": imagen.Motivo,
                "procesado": imagen.Procesado,
                "fecha_procesado": formatear_fecha_larga(imagen.FechaProcesado),
                "movimiento": {
                    "id": movimiento.Id,
                    "categoria": {
                        "id": movimiento.categoria.Id,
                        "nombre": movimiento.categoria.NombreCategoria,
                    } if movimiento.categoria else None,
                    "etiquetas": [
                        {
                            "id": enlace.EtiquetaId,
                            "nombre": enlace.etiqueta.NombreEtiqueta,
                        }
                        for enlace in movimiento.etiquetas
                    ],
                    "numero_factura": movimiento.NumeroFactura,
                    "empresa": {
                        "id": movimiento.empresa.Id,
                        "nombre": movimiento.empresa.NombreEmpresa,
                        "ruc": movimiento.empresa.Ruc,
                        "url_logo": movimiento.empresa.UrlLogo,
                    } if movimiento.empresa else None,
                    "total_gasto": movimiento.TotalGasto,
                } if (movimiento := imagen.movimiento) else None,
            }
            for imagen in imagenes
        ]
        return RespuestaFuncion(data_registro=respuesta)
    except Exception as e:
            await db.rollback()
            return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))

