OCR_DATA={
    "success": "true",
    "message": "Factura procesada correctamente",
    "data": {
        "empresa": "BIGGIE S.A.",
        "info":"",
        "ruc_empresa": "80077406-0",
        "fecha": "2025-08-10",
        "numero_factura": "252-002-0022401xxB",
        "total": 58600.0,
        "iva_diez": 3300.0,
        "iva_cinco": 1062.0,
        "fiabilidad": "Excelente",
        "detalle": [
            "Jugo Watts Nectar naranj",
            "Galletita Hogarenas Salv",
            "Jardinera verduras Norte",
            "Jardinera verduras Norte",
            "Yerba Kurupi con Anis Ca",
            "Manzanilla Arcoiris de 5",
            "Bolsa Biggie Camisilla Pead Blan"
        ],
        "Model": "gemini-3.5-flash",
        "success_registro":"False",
        "data_correct":"True"
    },
    "id_usuario": 1,
    "id_form": 0,
    "data_clasificacion": {
        "clasificacion": "Supermercados",
        "modelo_clasificador": "openai/gpt-oss-20b",
        "etiquetas": ['Alimentacion', 'Bebidas', 'Verduras', 'Yerba', 'Té']
    }
}

TESTS_DATA={
    "factura": {
        "empresa": "BIGGIE S.A.",
        "rubro": "",
        "ruc_empresa": "80077406-0",
        "fecha": "2025-08-10",
        "numero_factura": "252-002-0022401xxB",
        "total": 58600.0,
        "iva_diez": 3300.0,
        "iva_cinco": 1062.0,
        "fiabilidad": "Excelente",
        "detalle": [
            "Jugo Watts Nectar naranj",
            "Galletita Hogarenas Salv",
            "Jardinera verduras Norte",
            "Jardinera verduras Norte",
            "Yerba Kurupi con Anis Ca",
            "Manzanilla Arcoiris de 5",
            "Bolsa Biggie Camisilla Pead Blan"
        ],
        "Model": "gemini-3.5-flash",
        "success_registro": "true",
        "mensaje_error": "prueba de error",
        "data_correct": "true"
    },
    "clasificacion": {
        "categoria": "Supermercados",
        "etiquetas": [
            "Alimentacion",
            "Bebidas",
            "Verduras",
            "Yerba",
            "Té"
        ],
        "modelo_clasificador": "openai/gpt-oss-20b"
    },
    "imagenes": {
        "urls_img": [
            "https://finsense-dev-gastos.rafaelibarra.xyz/FIND_20260820_220509_00c684af.jpeg",
            "https://finsense-dev-gastos.rafaelibarra.xyz/FIND_20260820_220509_c3cbed4b.jpeg"
        ],
        "success": "true",
        "mensaje_error": ""
    }
}

DATA_RESUMEN={
  "2": [
    {
      "codigo_tarea": "U_2_F_2026_08_21_T_22_21_41",
      "id_reg": 77,
      "fecha_hora_procesado": "21/08/26 23:32:40"
    }
  ],
  "1": [
    {
      "codigo_tarea": "U_1_F_2026_08_21_T_22_57_35",
      "id_reg": 78,
      "fecha_hora_procesado": "21/08/26 23:36:39"
    },
    {
      "codigo_tarea": "U_1_F_2026_08_21_T_22_57_46",
      "id_reg": 79,
      "fecha_hora_procesado": "21/08/26 23:38:07"
    }
  ]
}

DATA_NEW_FORMAT={
    "factura": {
        "empresa": "CADENA REAL S.A",
        "rubro": "",
        "ruc_empresa": "80016951-4",
        "fecha": "2026-08-21",
        "numero_factura": "011-011-0225206",
        "total": 48726.0,
        "iva_diez": 4430.0,
        "iva_cinco": 0.0,
        "fiabilidad": "Excelente",
        "detalle": [
            "CHIPA MESTIZO X K",
            "SAND. LACTEADO IN",
            "ROSQUITA REAL X K",
            "GALLETITAS HOGARE",
            "BOLSA CAMISILLA 4"
        ],
        "Model": "gemini-3.5-flash",
        "success_registro": "true",
        "mensaje_error": "",
        "data_correct": "true"
    },
    "clasificacion": {
        "categoria": "Supermercados",
        "etiquetas": [
            {
                "etiqueta": "Alimentacion",
                "conceptos": [
                    "CHIPA MESTIZO X K",
                    "SAND. LACTEADO IN",
                    "ROSQUITA REAL X K",
                    "GALLETITAS HOGARE"
                ]
            },
            {
                "etiqueta": "Envases",
                "conceptos": [
                    "BOLSA CAMISILLA 4"
                ]
            }
        ],
        "modelo_clasificador": "qwen/qwen3.6-27b"
    },
    "imagenes": {
        "urls_img": [
            "https://finsense-dev-temporales.rafaelibarra.xyz/FIN_SENSE_DEV_20260828_210852_b63fc61f.jpeg"
        ],
        "success": "true",
        "mensaje_error": "",
        "tipo_url": "Temporal"
    },
    "tipo_registro": "Asistido"
}