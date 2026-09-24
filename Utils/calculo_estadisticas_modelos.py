from collections import defaultdict

from Schemas.ApisResponseSchemas.datos_modelos_response_shema import (
    TokensPorOperacionSchema,
    TokensPorModeloSchema,
    TokensPorDiaSchema,
    TokensPorMesSchema,
    TokensPorAñoSchema,
    DataTokensSchema,
    TokensTotalesSchema,
    TokensUsuarioSchema,
    TokensUsuarioPorOperacionSchema,
    TokensUsuarioPorModeloSchema,
    GastoUsuarioSchema,
    DataUsuarioItemSchema,
    DataUsuarioSchema,
    EstadisticasSchema,
    DatosEstadisticosSchema,
)


def calcular_estadisticas(valores):

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
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }

    # ==========================================================
    # TOKENS POR TIPO DE OPERACIÓN
    # ==========================================================

    por_tipo_operacion = defaultdict(
        lambda: {
            "InputTokens": 0,
            "OutputTokens": 0,
            "ThoughtsTokens": 0,
            "TotalTokens": 0,
        }
    )

    # ==========================================================
    # TOKENS POR MODELO
    #
    # Modelo
    #   ├── Resumen
    #   └── distribucion
    #          ├── Operacion 1
    #          └── Operacion 2
    # ==========================================================

    por_modelo = defaultdict(
        lambda: {
            "Resumen": {
                "InputTokens": 0,
                "OutputTokens": 0,
                "ThoughtsTokens": 0,
                "TotalTokens": 0,
            },
            "distribucion": defaultdict(
                lambda: {
                    "InputTokens": 0,
                    "OutputTokens": 0,
                    "ThoughtsTokens": 0,
                    "TotalTokens": 0,
                }
            ),
        }
    )

    # ==========================================================
    # TOKENS POR AÑO / MES / DÍA
    # ==========================================================

    por_fecha = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: {
                    "InputTokens": 0,
                    "OutputTokens": 0,
                    "ThoughtsTokens": 0,
                    "TotalTokens": 0,
                }
            )
        )
    )

    # ==========================================================
    # ESTADÍSTICAS POR USUARIO
    # ==========================================================

    por_usuario = defaultdict(
        lambda: {
            "tokens": {
                "InputTokens": 0,
                "OutputTokens": 0,
                "ThoughtsTokens": 0,
                "TotalTokens": 0,
            },
            "por_tipo_operacion": defaultdict(
                lambda: {
                    "InputTokens": 0,
                    "OutputTokens": 0,
                    "ThoughtsTokens": 0,
                    "TotalTokens": 0,
                }
            ),
            "por_modelo": defaultdict(
                lambda: {
                    "InputTokens": 0,
                    "OutputTokens": 0,
                    "ThoughtsTokens": 0,
                    "TotalTokens": 0,
                }
            ),
            "cantidad_registros": 0,
            "total_tamanno_img": 0,
            "por_gasto_registrado": {
                True: {
                    "cantidad_registros": 0,
                    "total_tamanno_img": 0,
                },
                False: {
                    "cantidad_registros": 0,
                    "total_tamanno_img": 0,
                },
            },
        }
    )

    # ==========================================================
    # RECORRER REGISTROS
    # ==========================================================

    for registro in valores:

        # ======================================================
        # DATOS DEL REGISTRO
        #
        # Estos datos se cuentan una sola vez por registro.
        # ======================================================

        nombre_usuario = (
            registro.usuario.UserName
            if registro.usuario
            else "Sin especificar"
        )

        tamanno_img = 0

        if registro.imagenes:
            tamanno_img = registro.imagenes[0].TamañoImagen or 0

        gasto_registrado = registro.movimiento is not None

        # ======================================================
        # CANTIDAD DE REGISTROS POR USUARIO
        # ======================================================

        por_usuario[nombre_usuario]["cantidad_registros"] += 1

        # ======================================================
        # TAMAÑO TOTAL DE IMÁGENES POR USUARIO
        # ======================================================

        por_usuario[nombre_usuario]["total_tamanno_img"] += tamanno_img

        # ======================================================
        # POR GASTO REGISTRADO
        # ======================================================

        datos_gasto = por_usuario[nombre_usuario][
            "por_gasto_registrado"
        ][gasto_registrado]

        datos_gasto["cantidad_registros"] += 1
        datos_gasto["total_tamanno_img"] += tamanno_img

        # ======================================================
        # DETALLES DEL REGISTRO
        # ======================================================

        for detalle in registro.detalles:

            input_tokens = detalle.InputTokens or 0
            output_tokens = detalle.OutputTokens or 0
            thoughts_tokens = detalle.ThoughtsTokens or 0
            total_tokens = detalle.TotalTokens or 0

            tipo_operacion = (
                detalle.TipoOperacion or "Sin especificar"
            )

            nombre_modelo = (
                detalle.NombreModelo or "Sin especificar"
            )

            fecha = detalle.FechaRegistro

            # ==================================================
            # TOTAL GENERAL
            # ==================================================

            total_general["InputTokens"] += input_tokens
            total_general["OutputTokens"] += output_tokens
            total_general["ThoughtsTokens"] += thoughts_tokens
            total_general["TotalTokens"] += total_tokens

            # ==================================================
            # POR TIPO DE OPERACIÓN
            # ==================================================

            por_tipo_operacion[tipo_operacion][
                "InputTokens"
            ] += input_tokens

            por_tipo_operacion[tipo_operacion][
                "OutputTokens"
            ] += output_tokens

            por_tipo_operacion[tipo_operacion][
                "ThoughtsTokens"
            ] += thoughts_tokens

            por_tipo_operacion[tipo_operacion][
                "TotalTokens"
            ] += total_tokens

            # ==================================================
            # POR MODELO - RESUMEN
            # ==================================================

            resumen = por_modelo[nombre_modelo]["Resumen"]

            resumen["InputTokens"] += input_tokens
            resumen["OutputTokens"] += output_tokens
            resumen["ThoughtsTokens"] += thoughts_tokens
            resumen["TotalTokens"] += total_tokens

            # ==================================================
            # POR MODELO - DISTRIBUCIÓN POR OPERACIÓN
            # ==================================================

            distribucion = por_modelo[nombre_modelo][
                "distribucion"
            ][tipo_operacion]

            distribucion["InputTokens"] += input_tokens
            distribucion["OutputTokens"] += output_tokens
            distribucion["ThoughtsTokens"] += thoughts_tokens
            distribucion["TotalTokens"] += total_tokens

            # ==================================================
            # POR FECHA
            # ==================================================

            if fecha:

                año = fecha.year
                mes = fecha.month
                dia = fecha.day

                datos_fecha = por_fecha[año][mes][dia]

                datos_fecha["InputTokens"] += input_tokens
                datos_fecha["OutputTokens"] += output_tokens
                datos_fecha["ThoughtsTokens"] += thoughts_tokens
                datos_fecha["TotalTokens"] += total_tokens

            # ==================================================
            # USUARIO - TOKENS
            # ==================================================

            tokens_usuario = por_usuario[nombre_usuario]["tokens"]

            tokens_usuario["InputTokens"] += input_tokens
            tokens_usuario["OutputTokens"] += output_tokens
            tokens_usuario["ThoughtsTokens"] += thoughts_tokens
            tokens_usuario["TotalTokens"] += total_tokens

            # ==================================================
            # USUARIO - POR TIPO DE OPERACIÓN
            # ==================================================

            usuario_operacion = por_usuario[nombre_usuario][
                "por_tipo_operacion"
            ][tipo_operacion]

            usuario_operacion["InputTokens"] += input_tokens
            usuario_operacion["OutputTokens"] += output_tokens
            usuario_operacion["ThoughtsTokens"] += thoughts_tokens
            usuario_operacion["TotalTokens"] += total_tokens

            # ==================================================
            # USUARIO - POR MODELO
            # ==================================================

            usuario_modelo = por_usuario[nombre_usuario][
                "por_modelo"
            ][nombre_modelo]

            usuario_modelo["InputTokens"] += input_tokens
            usuario_modelo["OutputTokens"] += output_tokens
            usuario_modelo["ThoughtsTokens"] += thoughts_tokens
            usuario_modelo["TotalTokens"] += total_tokens

    # ==========================================================
    # CONVERTIR POR TIPO DE OPERACIÓN
    # ==========================================================

    resultado_tipo_operacion = []

    for tipo, datos in por_tipo_operacion.items():

        resultado_tipo_operacion.append(
            TokensPorOperacionSchema(
                TipoOperacion=tipo,
                **datos
            )
        )

    # ==========================================================
    # CONVERTIR POR MODELO
    # ==========================================================

    resultado_modelo = []

    for nombre_modelo, datos_modelo in por_modelo.items():

        distribucion = []

        for tipo_operacion, datos in (
            datos_modelo["distribucion"].items()
        ):

            distribucion.append(
                TokensPorOperacionSchema(
                    TipoOperacion=tipo_operacion,
                    **datos
                )
            )

        resultado_modelo.append(
            TokensPorModeloSchema(
                NombreModelo=nombre_modelo,
                Resumen=TokensTotalesSchema(
                    **datos_modelo["Resumen"]
                ),
                distribucion=distribucion,
            )
        )

    # ==========================================================
    # CONVERTIR POR FECHA
    # ==========================================================

    resultado_fecha = []

    for año, meses in sorted(por_fecha.items()):

        datos_meses = []

        for mes in range(1, 13):

            dias = meses.get(mes, {})

            datos_dias = []

            for dia, datos in sorted(dias.items()):

                datos_dias.append(
                    TokensPorDiaSchema(
                        Dia=dia,
                        **datos
                    )
                )

            datos_meses.append(
                TokensPorMesSchema(
                    NumeroMes=mes,
                    Mes=Meses[mes],
                    datos=datos_dias,
                )
            )

        resultado_fecha.append(
            TokensPorAñoSchema(
                Año=año,
                datos=datos_meses,
            )
        )

    # ==========================================================
    # CONVERTIR DATOS POR USUARIO
    # ==========================================================

    resultado_usuarios = []

    for nombre_usuario, datos_usuario in por_usuario.items():

        tokens = datos_usuario["tokens"]

        # ======================================================
        # PORCENTAJES CONTRA EL TOTAL GENERAL
        # ======================================================

        porcentaje_input = round(
            tokens["InputTokens"] / total_general["InputTokens"] * 100
            if total_general["InputTokens"]
            else 0,
            2
        )

        porcentaje_output = round(
            tokens["OutputTokens"]
            / total_general["OutputTokens"]
            * 100
            if total_general["OutputTokens"]
            else 0,
            2
        )

        porcentaje_thoughts = round(
            tokens["ThoughtsTokens"]
            / total_general["ThoughtsTokens"]
            * 100
            if total_general["ThoughtsTokens"]
            else 0,
            2
        )

        porcentaje_total = round(
            tokens["TotalTokens"]
            / total_general["TotalTokens"]
            * 100
            if total_general["TotalTokens"]
            else 0,
            2
        )

        # ======================================================
        # TOKENS POR OPERACIÓN
        # ======================================================

        resultado_usuario_operacion = []

        for tipo_operacion, datos in (
            datos_usuario["por_tipo_operacion"].items()
        ):

            resultado_usuario_operacion.append(
                TokensUsuarioPorOperacionSchema(
                    TipoOperacion=tipo_operacion,
                    **datos
                )
            )

        # ======================================================
        # TOKENS POR MODELO
        # ======================================================

        resultado_usuario_modelo = []

        for nombre_modelo, datos in (
            datos_usuario["por_modelo"].items()
        ):

            resultado_usuario_modelo.append(
                TokensUsuarioPorModeloSchema(
                    NombreModelo=nombre_modelo,
                    **datos
                )
            )

        # ======================================================
        # POR GASTO REGISTRADO
        # ======================================================

        resultado_gasto = []

        for gasto_registrado in [True, False]:

            datos_gasto = datos_usuario[
                "por_gasto_registrado"
            ][gasto_registrado]

            resultado_gasto.append(
                GastoUsuarioSchema(
                    gasto_registrado=gasto_registrado,
                    cantidad_registros=datos_gasto[
                        "cantidad_registros"
                    ],
                    total_tamanno_img=datos_gasto[
                        "total_tamanno_img"
                    ],
                )
            )

        # ======================================================
        # USUARIO
        # ======================================================

        resultado_usuarios.append(
            DataUsuarioItemSchema(
                NombreUsuario=nombre_usuario,

                tokens=TokensUsuarioSchema(
                    InputTokens=tokens["InputTokens"],
                    OutputTokens=tokens["OutputTokens"],
                    ThoughtsTokens=tokens["ThoughtsTokens"],
                    TotalTokens=tokens["TotalTokens"],

                    PorcentajeInputTokens=porcentaje_input,
                    PorcentajeOutputTokens=porcentaje_output,
                    PorcentajeThoughtsTokens=porcentaje_thoughts,
                    PorcentajeTotalTokens=porcentaje_total,
                ),

                por_tipo_operacion=resultado_usuario_operacion,

                por_modelo=resultado_usuario_modelo,

                cantidad_registros=datos_usuario[
                    "cantidad_registros"
                ],

                total_tamanno_img=datos_usuario[
                    "total_tamanno_img"
                ],

                por_gasto_registrado=resultado_gasto,
            )
        )

    # ==========================================================
    # DETALLES DE REGISTROS
    # ==========================================================

    detalles_registros = [
        DatosEstadisticosSchema.model_validate(registro)
        for registro in valores
    ]

    # ==========================================================
    # DATA TOKENS
    # ==========================================================

    data_tokens = DataTokensSchema(
        total_general=TokensTotalesSchema(
            **total_general
        ),
        por_tipo_operacion=resultado_tipo_operacion,
        por_modelo=resultado_modelo,
        por_fecha=resultado_fecha,
    )

    # ==========================================================
    # DATA USUARIOS
    # ==========================================================

    data_usuarios = DataUsuarioSchema(
        datos=resultado_usuarios
    )

    # ==========================================================
    # RESULTADO FINAL
    # ==========================================================

    return EstadisticasSchema(
        data_tokens=data_tokens,
        data_usuarios=data_usuarios,
        detalles_registros=detalles_registros,
    )