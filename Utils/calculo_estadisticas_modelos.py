#.Utils/
from collections import defaultdict


def calcular_estadisticas(valores) -> dict:

    # ==========================================================
    # TOTAL GENERAL DE TOKENS
    # ==========================================================

    total_general = {
        "InputTokens": 0,
        "OutputTokens": 0,
        "ThoughtsTokens": 0,
        "TotalTokens": 0,
    }

    Meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }

    por_tipo_operacion = defaultdict(
        lambda: {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0}
    )

    por_modelo = defaultdict(
        lambda: {
            "Resumen": {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0},
            "distribucion": defaultdict(
                lambda: {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0}
            ),
        }
    )

    por_fecha = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0}
            )
        )
    )

    por_usuario = defaultdict(
        lambda: {
            "tokens": {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0},
            "por_tipo_operacion": defaultdict(
                lambda: {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0}
            ),
            "por_modelo": defaultdict(
                lambda: {"InputTokens": 0, "OutputTokens": 0, "ThoughtsTokens": 0, "TotalTokens": 0}
            ),
            "cantidad_registros": 0,
            "total_tamanno_img": 0,
            "por_gasto_registrado": {
                True: {"cantidad_registros": 0, "total_tamanno_img": 0},
                False: {"cantidad_registros": 0, "total_tamanno_img": 0},
            },
        }
    )

    # ==========================================================
    # RECORRER REGISTROS
    # ==========================================================

    for registro in valores:

        nombre_usuario = registro.usuario.UserName if registro.usuario else "Sin especificar"

        tamanno_img = 0
        if registro.imagenes:
            tamanno_img = registro.imagenes[0].TamañoImagen or 0

        por_usuario[nombre_usuario]["cantidad_registros"] += 1
        por_usuario[nombre_usuario]["total_tamanno_img"] += tamanno_img

        gasto_registrado = registro.movimiento is not None
        datos_gasto = por_usuario[nombre_usuario]["por_gasto_registrado"][gasto_registrado]
        datos_gasto["cantidad_registros"] += 1
        datos_gasto["total_tamanno_img"] += tamanno_img

        for detalle in registro.detalles:

            input_tokens = detalle.InputTokens or 0
            output_tokens = detalle.OutputTokens or 0
            thoughts_tokens = detalle.ThoughtsTokens or 0
            total_tokens = detalle.TotalTokens or 0

            tipo_operacion = detalle.TipoOperacion or "Sin especificar"
            nombre_modelo = detalle.NombreModelo or "Sin especificar"
            fecha = detalle.FechaRegistro

            # TOTAL GENERAL
            total_general["InputTokens"] += input_tokens
            total_general["OutputTokens"] += output_tokens
            total_general["ThoughtsTokens"] += thoughts_tokens
            total_general["TotalTokens"] += total_tokens

            # POR TIPO DE OPERACIÓN
            por_tipo_operacion[tipo_operacion]["InputTokens"] += input_tokens
            por_tipo_operacion[tipo_operacion]["OutputTokens"] += output_tokens
            por_tipo_operacion[tipo_operacion]["ThoughtsTokens"] += thoughts_tokens
            por_tipo_operacion[tipo_operacion]["TotalTokens"] += total_tokens

            # POR MODELO - RESUMEN
            resumen = por_modelo[nombre_modelo]["Resumen"]
            resumen["InputTokens"] += input_tokens
            resumen["OutputTokens"] += output_tokens
            resumen["ThoughtsTokens"] += thoughts_tokens
            resumen["TotalTokens"] += total_tokens

            # POR MODELO - DISTRIBUCIÓN POR OPERACIÓN
            distribucion = por_modelo[nombre_modelo]["distribucion"][tipo_operacion]
            distribucion["InputTokens"] += input_tokens
            distribucion["OutputTokens"] += output_tokens
            distribucion["ThoughtsTokens"] += thoughts_tokens
            distribucion["TotalTokens"] += total_tokens

            # POR FECHA
            if fecha:
                datos_fecha = por_fecha[fecha.year][fecha.month][fecha.day]
                datos_fecha["InputTokens"] += input_tokens
                datos_fecha["OutputTokens"] += output_tokens
                datos_fecha["ThoughtsTokens"] += thoughts_tokens
                datos_fecha["TotalTokens"] += total_tokens

            # USUARIO - TOKENS
            tokens_usuario = por_usuario[nombre_usuario]["tokens"]
            tokens_usuario["InputTokens"] += input_tokens
            tokens_usuario["OutputTokens"] += output_tokens
            tokens_usuario["ThoughtsTokens"] += thoughts_tokens
            tokens_usuario["TotalTokens"] += total_tokens

            # USUARIO - POR TIPO DE OPERACIÓN
            usuario_operacion = por_usuario[nombre_usuario]["por_tipo_operacion"][tipo_operacion]
            usuario_operacion["InputTokens"] += input_tokens
            usuario_operacion["OutputTokens"] += output_tokens
            usuario_operacion["ThoughtsTokens"] += thoughts_tokens
            usuario_operacion["TotalTokens"] += total_tokens

            # USUARIO - POR MODELO
            usuario_modelo = por_usuario[nombre_usuario]["por_modelo"][nombre_modelo]
            usuario_modelo["InputTokens"] += input_tokens
            usuario_modelo["OutputTokens"] += output_tokens
            usuario_modelo["ThoughtsTokens"] += thoughts_tokens
            usuario_modelo["TotalTokens"] += total_tokens

    # ==========================================================
    # CONVERTIR POR TIPO DE OPERACIÓN -> lista de dicts
    # ==========================================================

    resultado_tipo_operacion = [
        {"TipoOperacion": tipo, **datos}
        for tipo, datos in por_tipo_operacion.items()
    ]

    # ==========================================================
    # CONVERTIR POR MODELO -> lista de dicts
    # ==========================================================

    resultado_modelo = []
    for nombre_modelo, datos_modelo in por_modelo.items():
        distribucion = [
            {"TipoOperacion": tipo_operacion, **datos}
            for tipo_operacion, datos in datos_modelo["distribucion"].items()
        ]
        resultado_modelo.append({
            "NombreModelo": nombre_modelo,
            "Resumen": dict(datos_modelo["Resumen"]),
            "distribucion": distribucion,
        })

    # ==========================================================
    # CONVERTIR POR FECHA -> lista de dicts (año/mes/día)
    # ==========================================================

    resultado_fecha = []
    for año, meses in sorted(por_fecha.items()):
        datos_meses = []
        for mes in range(1, 13):
            dias = meses.get(mes, {})
            datos_dias = [
                {"Dia": dia, **datos}
                for dia, datos in sorted(dias.items())
            ]
            datos_meses.append({
                "NumeroMes": mes,
                "Mes": Meses[mes],
                "datos": datos_dias,
            })
        resultado_fecha.append({"Año": año, "datos": datos_meses})

    # ==========================================================
    # CONVERTIR DATOS POR USUARIO -> lista de dicts
    # ==========================================================

    resultado_usuarios = []
    for nombre_usuario, datos_usuario in por_usuario.items():

        tokens = datos_usuario["tokens"]

        porcentaje_input = round(
            tokens["InputTokens"] / total_general["InputTokens"] * 100
            if total_general["InputTokens"] else 0, 2
        )
        porcentaje_output = round(
            tokens["OutputTokens"] / total_general["OutputTokens"] * 100
            if total_general["OutputTokens"] else 0, 2
        )
        porcentaje_thoughts = round(
            tokens["ThoughtsTokens"] / total_general["ThoughtsTokens"] * 100
            if total_general["ThoughtsTokens"] else 0, 2
        )
        porcentaje_total = round(
            tokens["TotalTokens"] / total_general["TotalTokens"] * 100
            if total_general["TotalTokens"] else 0, 2
        )

        resultado_usuario_operacion = [
            {"TipoOperacion": tipo_operacion, **datos}
            for tipo_operacion, datos in datos_usuario["por_tipo_operacion"].items()
        ]

        resultado_usuario_modelo = [
            {"NombreModelo": nombre_modelo, **datos}
            for nombre_modelo, datos in datos_usuario["por_modelo"].items()
        ]

        resultado_gasto = [
            {
                "gasto_registrado": gasto_registrado,
                "cantidad_registros": datos_usuario["por_gasto_registrado"][gasto_registrado]["cantidad_registros"],
                "total_tamanno_img": datos_usuario["por_gasto_registrado"][gasto_registrado]["total_tamanno_img"],
            }
            for gasto_registrado in [True, False]
        ]

        resultado_usuarios.append({
            "NombreUsuario": nombre_usuario,
            "tokens": {
                **tokens,
                "PorcentajeInputTokens": porcentaje_input,
                "PorcentajeOutputTokens": porcentaje_output,
                "PorcentajeThoughtsTokens": porcentaje_thoughts,
                "PorcentajeTotalTokens": porcentaje_total,
            },
            "por_tipo_operacion": resultado_usuario_operacion,
            "por_modelo": resultado_usuario_modelo,
            "cantidad_registros": datos_usuario["cantidad_registros"],
            "total_tamanno_img": datos_usuario["total_tamanno_img"],
            "por_gasto_registrado": resultado_gasto,
        })

    # ==========================================================
    # RESULTADO FINAL (dict plano, sin Schemas)
    # ==========================================================

    return {
        "data_tokens": {
            "total_general": dict(total_general),
            "por_tipo_operacion": resultado_tipo_operacion,
            "por_modelo": resultado_modelo,
            "por_fecha": resultado_fecha,
        },
        "data_usuarios": {
            "datos": resultado_usuarios,
        },
    }