#.Utils/
from collections import defaultdict
from Utils.formateo_fechas import formatear_fecha_larga
from Utils.obtener_tamanno_img_Mb import calcular_mb

TEMPLATE_A_TIPO_CORREO = {
    "registro_pendiente.html": "ImagenesPendientes",
    "urls_temp_eliminadas.html": "EliminacionUrlsTemp",
}


def resumen_datos_tareas(valores) -> dict:

    return {
        "imagenes_pendientes": _resumen_imagenes_pendientes(valores["imagenes_pendientes"]),
        "urls_imagenes_temporales": _resumen_urls_imagenes_temporales(
            valores["urls_imagenes_temporales"]
        ),
        "envio_correos": _resumen_envio_correos(valores["envio_correos"]),
    }


# ==============================================================
# IMAGENES PENDIENTES
# ==============================================================

def _resumen_imagenes_pendientes(registros) -> dict:

    por_tarea = defaultdict(
        lambda: {
            "urls": [],
            "cantidad_registros": 0,
            "total_tamanno_imagen": 0,
            "fechas_registro": [],
            "fechas_procesado": [],
            "procesado": [],
            "usuario": None,
        }
    )

    for registro in registros:

        grupo = por_tarea[registro.CodigoTarea]

        tamanno = registro.TamañoImagen or 0

        grupo["cantidad_registros"] += 1
        grupo["total_tamanno_imagen"] += tamanno
        grupo["urls"].append({"Url": registro.UrlImagen, "TamañoImagen": tamanno})

        if registro.FechaRegistro:
            grupo["fechas_registro"].append(registro.FechaRegistro)

        if registro.FechaProcesado:
            grupo["fechas_procesado"].append(registro.FechaProcesado)

        grupo["procesado"].append(bool(registro.Procesado))
        grupo["usuario"] = registro.usuario.UserName if registro.usuario else None

    detalle = []

    for codigo_tarea, datos in por_tarea.items():

        fecha_registro_mayor = max(datos["fechas_registro"], default=None)
        fecha_procesado_mayor = max(datos["fechas_procesado"], default=None)

        detalle.append({
            "CodigoTarea": codigo_tarea,
            "CantidadRegistros": datos["cantidad_registros"],
            "TotalTamannoImagen": datos["total_tamanno_imagen"],
            "TotalTamannoImagen_MB": calcular_mb(datos["total_tamanno_imagen"]),
            "Urls": datos["urls"],
            "FechaRegistro": formatear_fecha_larga(fecha_registro_mayor) if fecha_registro_mayor else None,
            "FechaProcesado": formatear_fecha_larga(fecha_procesado_mayor) if fecha_procesado_mayor else None,
            "UserName": datos["usuario"],
            "Procesado": all(datos["procesado"]) if datos["procesado"] else False,
        })

    total_pendientes = {
        "CantidadTareas": len(detalle),
        "TotalTamannoImagenes": sum(item["TotalTamannoImagen"] for item in detalle),
        
        "CantidadImagenes": sum(item["CantidadRegistros"] for item in detalle),
    }
    total_pendientes["TotalTamannoImagen_MB"] = calcular_mb(total_pendientes["TotalTamannoImagenes"])

    por_procesado = {
        procesado: {"CantidadTareas": 0, "TotalTamannoImagenes": 0, "CantidadImagenes": 0}
        for procesado in (False, True)
    }

    for item in detalle:
        grupo = por_procesado[item["Procesado"]]
        grupo["CantidadTareas"] += 1
        grupo["TotalTamannoImagenes"] += item["TotalTamannoImagen"]
        grupo["CantidadImagenes"] += item["CantidadRegistros"]

    for procesado, datos in por_procesado.items():
        datos["TotalTamannoImagen_MB"] = calcular_mb(datos["TotalTamannoImagenes"])

    total_por_procesado = [
        {"Procesado": procesado, **datos}
        for procesado, datos in por_procesado.items()
    ]

    usuarios_distintos = sorted({item["UserName"] for item in detalle if item["UserName"]})

    resumen = {
        "TotalPendientes": total_pendientes,
        "TotalPorProcesado": total_por_procesado,
        "Usuarios": {
            "CantidadUsuarios": len(usuarios_distintos),
            "Usuarios": usuarios_distintos,
        },
    }

    return {"detalle": detalle, "Resumen": resumen}


# ==============================================================
# URLS DE IMAGENES TEMPORALES
# ==============================================================

def _resumen_urls_imagenes_temporales(registros) -> dict:

    por_proceso = defaultdict(
        lambda: {
            "urls": [],
            "cantidad_registros": 0,
            "total_tamanno_imagen": 0,
            "fechas_registro": [],
            "fechas_procesado": [],
            "fechas_eliminacion": [],
            "pendiente_eliminacion": [],
            "usuario": None,
        }
    )

    for registro in registros:
        grupo = por_proceso[registro.CodigoProceso]
        tamanno = registro.TamañoImagen or 0

        grupo["cantidad_registros"] += 1
        grupo["total_tamanno_imagen"] += tamanno
        grupo["urls"].append({"Url": registro.UrlImagen, "TamañoImagen": tamanno})

        if registro.FechaRegistro:
            grupo["fechas_registro"].append(registro.FechaRegistro)

        if registro.FechaProcesado:
            grupo["fechas_procesado"].append(registro.FechaProcesado)

        if registro.FechaEliminacion:
            grupo["fechas_eliminacion"].append(registro.FechaEliminacion)

        grupo["pendiente_eliminacion"].append(bool(registro.PendienteEliminacion))
        grupo["usuario"] = registro.usuario.UserName if registro.usuario else None

    detalle = []

    for codigo_proceso, datos in por_proceso.items():
        fecha_registro_mayor = max(datos["fechas_registro"], default=None)
        fecha_procesado_mayor = max(datos["fechas_procesado"], default=None)
        fecha_eliminacion_mayor = max(datos["fechas_eliminacion"], default=None)

        detalle.append({
            "CodigoProceso": codigo_proceso,
            "CantidadRegistros": datos["cantidad_registros"],
            "TotalTamannoImagen": datos["total_tamanno_imagen"],
            "TotalTamannoImagen_MB": calcular_mb(datos["total_tamanno_imagen"]),
            "Urls": datos["urls"],
            "FechaRegistro": formatear_fecha_larga(fecha_registro_mayor) if fecha_registro_mayor else None,
            "FechaProcesado": formatear_fecha_larga(fecha_procesado_mayor) if fecha_procesado_mayor else None,
            "FechaEliminacion": formatear_fecha_larga(fecha_eliminacion_mayor) if fecha_eliminacion_mayor else None,
            "UserName": datos["usuario"],
            "PendienteEliminacion": all(datos["pendiente_eliminacion"]),
        })

    total_urls_temporales = {
        "CantidadProcesos": len(detalle),
        "TotalTamannoImagenes": sum(item["TotalTamannoImagen"] for item in detalle),
        "CantidadImagenes": sum(item["CantidadRegistros"] for item in detalle),
    }
    total_urls_temporales["TotalTamannoImagen_MB"] = calcular_mb(
        total_urls_temporales["TotalTamannoImagenes"]
    )

    por_pendiente_eliminacion = {
        pendiente: {
            "CantidadProcesos": 0,
            "TotalTamannoImagenes": 0,
            "CantidadImagenes": 0,
        }
        for pendiente in (False, True)
    }

    for item in detalle:
        grupo = por_pendiente_eliminacion[item["PendienteEliminacion"]]
        grupo["CantidadProcesos"] += 1
        grupo["TotalTamannoImagenes"] += item["TotalTamannoImagen"]
        grupo["CantidadImagenes"] += item["CantidadRegistros"]

    for datos in por_pendiente_eliminacion.values():
        datos["TotalTamannoImagen_MB"] = calcular_mb(datos["TotalTamannoImagenes"])

    total_por_pendiente_eliminacion = [
        {"PendienteEliminacion": pendiente, **datos}
        for pendiente, datos in por_pendiente_eliminacion.items()
    ]

    usuarios_distintos = sorted({
        item["UserName"] for item in detalle if item["UserName"]
    })

    resumen = {
        **total_urls_temporales,
        "CantidadPendientesEliminacion": sum(
            item["CantidadRegistros"]
            for item in detalle
            if item["PendienteEliminacion"]
        ),
        "TotalPorPendienteEliminacion": total_por_pendiente_eliminacion,
        "Usuarios": {
            "CantidadUsuarios": len(usuarios_distintos),
            "Usuarios": usuarios_distintos,
        },
    }

    return {"detalle": detalle, "Resumen": resumen}


# ==============================================================
# ENVIO DE CORREOS
# ==============================================================

def _resumen_envio_correos(registros) -> dict:

    detalle = []

    for registro in registros:

        username = registro.usuario.UserName if registro.usuario else None
        tipo_correo = TEMPLATE_A_TIPO_CORREO.get(registro.NombreTemplate, "Desconocido")
        tipo_destinatario = "Administrador" if username is None else "UsuarioAplicacion"

        detalle.append({
            "Destinatario": registro.Destinatario,
            "Asunto": registro.Asunto,
            "Data": registro.Data,
            "FechaRegistro": formatear_fecha_larga(registro.FechaRegistro),
            "Procesado": registro.Procesado,
            "Id": registro.Id,
            "NombreTemplate": registro.NombreTemplate,
            "ContextKey": registro.ContextKey,
            "FechaProcesado": formatear_fecha_larga(registro.FechaProcesado),
            "UsuarioId": registro.UsuarioId,
            "usuario": username,
            "TipoCorreo": tipo_correo,
            "TipoDestinatario": tipo_destinatario,
        })

    por_procesado_general = {False: 0, True: 0}
    for item in detalle:
        por_procesado_general[item["Procesado"]] += 1

    cantidad_por_procesado = [
        {"Procesado": procesado, "Cantidad": cantidad}
        for procesado, cantidad in por_procesado_general.items()
    ]

    por_tipo_correo = defaultdict(lambda: {"total": 0, "por_procesado": defaultdict(int)})
    for item in detalle:
        grupo = por_tipo_correo[item["TipoCorreo"]]
        grupo["total"] += 1
        grupo["por_procesado"][item["Procesado"]] += 1

    resultado_tipo_correo = [
        {
            "TipoCorreo": tipo,
            "CantidadTotal": datos["total"],
            "CantidadPorProcesado": [
                {"Procesado": procesado, "Cantidad": cantidad}
                for procesado, cantidad in datos["por_procesado"].items()
            ],
        }
        for tipo, datos in por_tipo_correo.items()
    ]

    por_tipo_destinatario = defaultdict(lambda: {"total": 0, "por_procesado": defaultdict(int)})
    for item in detalle:
        grupo = por_tipo_destinatario[item["TipoDestinatario"]]
        grupo["total"] += 1
        grupo["por_procesado"][item["Procesado"]] += 1

    resultado_tipo_destinatario = [
        {
            "TipoDestinatario": tipo,
            "CantidadTotal": datos["total"],
            "CantidadPorProcesado": [
                {"Procesado": procesado, "Cantidad": cantidad}
                for procesado, cantidad in datos["por_procesado"].items()
            ],
        }
        for tipo, datos in por_tipo_destinatario.items()
    ]

    usuarios_distintos = sorted({item["usuario"] for item in detalle if item["usuario"]})

    por_estado = defaultdict(int)
    for item in detalle:
        if item["TipoCorreo"] != "ImagenesPendientes":
            continue
        for dato in (item["Data"] or []):
            estado = dato.get("estado", "Sin estado")
            por_estado[estado] += 1

    total_por_estado_imagenes_pendientes = [
        {"estado": estado, "Cantidad": cantidad} for estado, cantidad in por_estado.items()
    ]

    resumen = {
        "CantidadTotalRegistros": len(detalle),
        "CantidadPorProcesado": cantidad_por_procesado,
        "PorTipoCorreo": resultado_tipo_correo,
        "PorTipoDestinatario": resultado_tipo_destinatario,
        "Usuarios": {
            "CantidadUsuarios": len(usuarios_distintos),
            "Usuarios": usuarios_distintos,
        },
        "TotalPorEstadoImagenesPendientes": total_por_estado_imagenes_pendientes,
    }

    return {"detalle": detalle, "Resumen": resumen}
