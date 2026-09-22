from collections import defaultdict
from Schemas.ApisResponseSchemas.datos_modelos_response_shema import (TokensPorOperacionSchema,TokensPorModeloSchema,
                                                                      TokensPorDiaSchema,TokensPorMesSchema,TokensPorAñoSchema,
                                                                      DataTokensSchema,TokensTotalesSchema)

def calcular_data_tokens(valores):

    # -----------------------------------
    # TOTAL GENERAL
    # -----------------------------------

    total_general = {
        "InputTokens": 0,
        "OutputTokens": 0,
        "ThoughtsTokens": 0,
        "TotalTokens": 0,
    }

    # -----------------------------------
    # POR TIPO DE OPERACIÓN
    # -----------------------------------

    por_tipo_operacion = defaultdict(
        lambda: {
            "InputTokens": 0,
            "OutputTokens": 0,
            "ThoughtsTokens": 0,
            "TotalTokens": 0,
        }
    )

    # -----------------------------------
    # POR MODELO
    # -----------------------------------

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

    # -----------------------------------
    # POR AÑO / MES / DÍA
    # -----------------------------------

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

    # -----------------------------------
    # RECORRER REGISTROS
    # -----------------------------------

    for registro in valores:

        for detalle in registro.detalles:

            input_tokens = detalle.InputTokens or 0
            output_tokens = detalle.OutputTokens or 0
            thoughts_tokens = detalle.ThoughtsTokens or 0
            total_tokens = detalle.TotalTokens or 0

            tipo_operacion = detalle.TipoOperacion or "Sin especificar"
            nombre_modelo = detalle.NombreModelo or "Sin especificar"

            fecha = detalle.FechaRegistro

            # ==================================================
            # TOTAL GENERAL
            # ==================================================

            total_general["InputTokens"] += input_tokens
            total_general["OutputTokens"] += output_tokens
            total_general["ThoughtsTokens"] += thoughts_tokens
            total_general["TotalTokens"] += total_tokens

            # ==================================================
            # POR TIPO DE OPERACION
            # ==================================================

            por_tipo_operacion[tipo_operacion]["InputTokens"] += input_tokens
            por_tipo_operacion[tipo_operacion]["OutputTokens"] += output_tokens
            por_tipo_operacion[tipo_operacion]["ThoughtsTokens"] += thoughts_tokens
            por_tipo_operacion[tipo_operacion]["TotalTokens"] += total_tokens

            # ==================================================
            # POR MODELO - RESUMEN
            # ==================================================

            resumen = por_modelo[nombre_modelo]["Resumen"]

            resumen["InputTokens"] += input_tokens
            resumen["OutputTokens"] += output_tokens
            resumen["ThoughtsTokens"] += thoughts_tokens
            resumen["TotalTokens"] += total_tokens

            # ==================================================
            # POR MODELO - DISTRIBUCION POR OPERACION
            # ==================================================

            distribucion = por_modelo[nombre_modelo]["distribucion"][tipo_operacion]

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

        # -----------------------------------
    # CONVERTIR POR TIPO OPERACIÓN
    # -----------------------------------

    resultado_tipo_operacion = []

    for tipo, datos in por_tipo_operacion.items():

        resultado_tipo_operacion.append(
            TokensPorOperacionSchema(
                TipoOperacion=tipo,
                **datos
            )
        )
    resultado_modelo = []

    for nombre_modelo, datos_modelo in por_modelo.items():

        distribucion = []

        for tipo_operacion, datos in datos_modelo["distribucion"].items():

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
        # -----------------------------------
    # CONVERTIR POR FECHA
    # -----------------------------------

    resultado_fecha = []

    for año, meses in sorted(por_fecha.items()):

        datos_meses = []

        for mes, dias in sorted(meses.items()):

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
                    Mes=mes,
                    datos=datos_dias
                )
            )

        resultado_fecha.append(
            TokensPorAñoSchema(
                Año=año,
                datos=datos_meses
            )
        )

    return DataTokensSchema(
        total_general=TokensTotalesSchema(
            **total_general
        ),
        por_tipo_operacion=resultado_tipo_operacion,
        por_modelo=resultado_modelo,
        por_fecha=resultado_fecha
    )    