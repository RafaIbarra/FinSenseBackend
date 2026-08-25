from google import genai
from google.genai import types
import json
from pydantic import BaseModel
from typing import List, Optional
from Config.settings import settings
from Repositories.errores_modelos import registro_error
from Schemas.integrations_schemas import FacturaExtraida

GEMINI_API_KEY = settings.GEMINI_API_KEY
client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODELS=[
            "gemini-3.5-flash",
            "gemini-2.5-flash",
            "gemini-3.1-flash-lite"
        ]




class CamposNoDetectadosError(Exception):
    """
    Se lanza cuando el modelo devolvió JSON válido pero ninguno de los campos clave
    (empresa, ruc_empresa, fecha, numero_factura, total) fue detectado — típicamente
    porque la imagen no corresponde a una factura. Permite que extraer_factura siga
    probando con el resto de GEMINI_MODELS antes de darse por vencido.
    """
    pass


# ── Prompt optimizado ─────────────────────────────────────
SYSTEM_PROMPT = """
Eres un extractor experto de datos de facturas. Analiza la imagen y devuelve ÚNICAMENTE un JSON válido.

ESTRUCTURA DE RESPUESTA:
{
  "empresa": "nombre del vendedor/empresa",
  "rubro": "rubro/actividad de la empresa tal cual aparece en la factura, o vacio si no aparece",
  "ruc_empresa": "4545454-4",
  "fecha": "YYYY-MM-DD",
  "numero_factura": "001-001-0000001",
  "total": 123.45,
  "iva_diez": 55.00,
  "iva_cinco": 11.00,
  "fiabilidad": "Excelente",
  "detalle": ["Leche Entera 1L", "Pan Integral", "Café Molido 250g"]
}

INSTRUCCIONES DE DETECCIÓN POR CAMPO:

1. EMPRESA:
   - Puede que no figure etiqueta como "Empresa" o "Razón Social".
   - Generalmente está en la parte SUPERIOR de la factura, en letras MÁS GRANDES que el resto del texto.
   - Busca el nombre comercial más prominente, usualmente en negrita o tamaño mayor.
   - Si hay varios nombres, prioriza el del vendedor/emisor (no el del cliente).

2. RUBRO:
   - Este campo busca capturar una frase o texto CORTO que indique a qué se dedica la empresa
     (su rubro/actividad), SOLO SI ese texto aparece explícitamente impreso en la factura.
   - Generalmente se ubica JUSTO DEBAJO del nombre de la empresa o JUSTO DEBAJO/AL LADO del logo,
     en letra más chica que el nombre comercial. Ejemplos de lo que puede aparecer ahí:
     "Supermercado", "Distribuidora de alimentos", "Farmacia y Perfumería", "Ferretería Industrial",
     "Venta de repuestos automotores", "Administración Nacional de Electricidad", etc.
   - REGLA CRÍTICA - NO INVENTAR: la gran mayoría de las facturas NO incluyen este dato. Extraé este
     campo ÚNICAMENTE si el texto está literalmente escrito e impreso en la imagen. NO deduzcas ni
     infieras el rubro a partir del nombre de la empresa, del tipo de productos vendidos, ni de
     ningún otro razonamiento. Este campo es una transcripción, no una inferencia.
   - No confundas esto con: la dirección, el teléfono, el email, el sitio web, el eslogan/lema
     publicitario sin relación al rubro, ni con el nombre de la empresa en sí.
   - Si tenés cualquier duda sobre si el texto realmente describe el rubro de la empresa, o si
     simplemente no aparece nada de esto en la imagen, devolvé "" (string vacío).
   - Nunca uses null para este campo: si no se encuentra, el valor debe ser exactamente "".

3. RUC_EMPRESA:
   - Busca etiquetas como: RUC, Nº RUC, Nro. RUC, Numero RUC, R.U.C., N° RUC, RUC Nº.
   - El formato suele ser numérico, a veces con guiones (ej: 1234567-8).
   - Extrae SOLO el número, sin la etiqueta.
   - IMPORTANTE - No confundir con el RUC/CI del CLIENTE: en muchas facturas (especialmente de servicios
     públicos como ANDE, ESSAP, COPACO) aparecen DOS identificadores similares:
       a) El RUC del EMISOR/EMPRESA, que casi siempre está pegado al logo o nombre comercial, en la
          cabecera superior de la factura (ej: debajo del logo, formato "RUC 80009735-1").
       b) Un campo "RUC/CI" más abajo, junto a los datos del cliente/titular ("Nombre", "Dirección",
          "Tit. Contrato"), que corresponde al RUC o Cédula de Identidad del CLIENTE, no de la empresa.
     Prioriza SIEMPRE el RUC ubicado junto al logo/nombre comercial del emisor como "ruc_empresa".
     El campo "RUC/CI" del cliente NO debe usarse para ruc_empresa.

4. FECHA:
   - Busca etiquetas como: Fecha, Fecha de Inicio, Fecha Factura, Fecha Emisión, Fecha de Emisión, Fec., Emisión.
   - Formato de salida SIEMPRE: YYYY-MM-DD.
   - Si la fecha está en formato DD/MM/YYYY o similar, conviértela.

5. NUMERO_FACTURA:
   - Busca etiquetas como: Nro Factura, Nº Factura, Nro. Factura, Factura Nº, No. Factura, N° de Factura,
     Factura crédito Nro., Documento Nro.
   - Formato típico (facturas comerciales estándar): XXX-XXX-XXXXXXX (tres grupos separados por guiones).
     Ejemplo: 001-001-0001234
   - FALLBACK - facturas especiales (ej: ANDE, ESSAP, COPACO y otras de servicios): el número de factura
     puede NO tener el formato XXX-XXX-XXXXXXX y en su lugar ser un código alfanumérico distinto
     (ej: "0010653595209AA" bajo la etiqueta "Factura crédito Nro."). En ese caso, extrae el valor TAL
     CUAL aparece junto a la etiqueta correspondiente, sin intentar forzarlo al formato de tres grupos.
   - Si hay varias etiquetas candidatas ("Nro. Timbrado", "Nro. Edición", "N.I.R.", etc.), NO las uses
     para numero_factura; solo usa la que esté explícitamente asociada a "Factura".

6. TOTAL:
   - Busca etiquetas como: Total, Total a Pagar, Total General, Importe Total, Total Gs., Total $, Total USD.
   - Extrae el valor numérico SIN símbolo de moneda.
   - Prioriza el total FINAL (el último/más grande), no subtotales.
   - CASO ESPECIAL - facturas con comisión (ej: ANDE y otras facturas de servicios con recargo por
     forma de pago): puede haber varios "totales" en la misma factura, como "TOTAL SIN COMISION" y
     "TOTAL CON COMISION". Usa esta prioridad de mayor a menor:
       1) "Total a Pagar" (si existe explícitamente con ese nombre)
       2) "Total con Comisión" / "Total Final" (el monto que el cliente realmente debe abonar,
          incluyendo comisiones o recargos)
       3) "Total" / "Total General" genérico
       4) "Total sin Comisión" / subtotales (usar solo si no hay ninguna opción anterior)
     El campo "total" siempre debe reflejar el monto FINAL que el cliente paga, no un subtotal previo
     a comisiones o recargos.

7. IVA_DIEZ (IVA 10%):
   - Busca etiquetas como: IVA 10%, IVA 10, I.V.A. 10%, Impuesto 10%, IVA Diez, IVA 10% Liquidación.
   - Extrae el monto numérico correspondiente al IVA al 10%.
   - Si no aparece, devuelve 0.0.

8. IVA_CINCO (IVA 5%):
   - Busca etiquetas como: IVA 5%, IVA 5, I.V.A. 5%, Impuesto 5%, IVA Cinco, IVA 5% Liquidación.
   - Extrae el monto numérico correspondiente al IVA al 5%.
   - Si no aparece, devuelve 0.0.

8.b IVA GENÉRICO (sin desglose de tasa):
   - Algunas facturas (comúnmente de servicios como ANDE) muestran una única línea genérica "I.V.A."
     SIN indicar si corresponde a 10% o 5%.
   - En ese caso, asume que corresponde a IVA 10% y coloca el monto en "iva_diez"; "iva_cinco" queda en 0.0.
   - Si la factura no menciona ningún IVA, "iva_diez" e "iva_cinco" deben ser 0.0 (nunca null).

9. DETALLE (lista de conceptos de artículos):
   - Busca la sección de artículos/conceptos/descripción de la factura, generalmente en formato de tabla o grilla.
   - Etiquetas comunes de la sección: Artículos, Conceptos, Descripción, Detalle, Productos, Items, Mercaderías, Servicios.
   - Extrae SOLO el nombre/concepto/descripción de cada artículo. NO incluyas cantidades, precios unitarios, totales por línea, códigos de barrar ni números de ítem.
   - Ejemplo de entrada en factura:
     "1  Leche Entera 1L    5.000    5.000"
     "2  Pan Integral       3.000    3.000"
   - Ejemplo de salida: ["Leche Entera 1L", "Pan Integral"]
   - Si un artículo tiene descripción larga que ocupa varias líneas, únelo en un solo string.
   - Si no hay artículos detectados, devuelve una lista vacía [].
   - Ignora filas de totales, subtotales, descuentos globales o textos como "Total de items".
   - Ignora también filas de impuestos (I.V.A., IVA 10%, IVA 5%), comisiones y ajustes de redondeo;
     esos NO son conceptos/artículos y no deben incluirse en "detalle".
   - En facturas de servicios (ej: ANDE), los conceptos de facturación (ej: "Alumbrado Publico",
     "Dif Consumo Minimo", "Energia Activa") SÍ cuentan como items válidos para "detalle".

10. FIABILIDAD (campo obligatorio):
   Evalúa qué tan seguro estás de la extracción basándote en:
   - Nitidez de la imagen
   - Claridad del texto
   - Si los campos clave (empresa, total, fecha) son legibles
   - Si hay ambigüedades o partes borrosas

   Clasifica EXACTAMENTE como una de estas tres opciones:
   - "Excelente": Imagen nítida, todo el texto es perfectamente legible, sin dudas.
   - "Bueno": Imagen aceptable, la mayoría legible, pero algún campo requirió inferencia o está algo borroso.
   - "Malo": Imagen borrosa, poca luz, texto ilegible, o falta información crítica. Los datos extraídos pueden ser incorrectos.

REGLAS GENERALES:
- Si no encuentras un campo, usa null (no omitas la clave), EXCEPTO "iva_diez" e "iva_cinco" que
  usan 0.0 en vez de null cuando no aplican o no aparecen (ver regla específica más abajo), y EXCEPTO
  "info" que usa "" (string vacío) en vez de null cuando no aparece en la imagen (ver regla 2).
- El campo "info" NUNCA debe ser una inferencia o suposición: o es una transcripción de un texto que
  realmente está impreso en la factura, o es "".
- Los valores numéricos deben ser números (float o int), NUNCA strings con símbolos.
- La fecha SIEMPRE en formato ISO: YYYY-MM-DD.
- El campo "detalle" SIEMPRE debe ser un array de strings, nunca null.
- "iva_diez" e "iva_cinco" NUNCA deben ser null: si no aplica o no aparece, usa 0.0.
  Si la factura menciona un único IVA genérico sin especificar tasa, ese monto va en "iva_diez"
  y "iva_cinco" queda en 0.0.
- Responde SOLO con el JSON, sin markdown, sin explicaciones, sin texto adicional.
"""


def _limpiar_respuesta(raw_text: str, model: Optional[str] = None) -> dict:
    """Limpia la respuesta de Gemini removiendo markdown y parseando JSON.

    Si se proporciona `model`, lo agrega como la clave `Model` en el dict parseado.
    """
    raw_text = raw_text.strip()
    raw_text = raw_text.removeprefix("```json").removeprefix("```")
    raw_text = raw_text.removesuffix("```").strip()
    data = json.loads(raw_text)
    if model is not None:
        # Añadir la info del modelo utilizado
        try:
            # Si ya existe una clave 'Model', sobrescribirla
            data["Model"] = model
        except Exception:
            data.update({"Model": model})
    return data


def _crear_parte_imagen(image_bytes: bytes, mime_type: str = "image/jpeg") -> types.Part:
    """Crea un Part de Gemini a partir de bytes."""
    return types.Part(
        inline_data=types.Blob(
            mime_type=mime_type,
            data=image_bytes
        )
    )


def _campo_vacio(valor) -> bool:
    """
    Determina si un valor debe considerarse "no detectado", más allá de ser
    estrictamente None. Cubre placeholders típicos que un modelo puede devolver
    en vez de null cuando no encuentra el dato (string vacío, espacios, "N/A", etc.).
    """
    if valor is None:
        return True
    if isinstance(valor, str):
        v = valor.strip().lower()
        return v in ("", "n/a", "na", "null", "none", "no aplica", "desconocido", "-")
    return False


async def _extraer_con_modelo(modelo: str, parts: list, time_out: int) -> FacturaExtraida:
    """
    Intenta extraer los datos de la factura usando un modelo específico de Gemini.
    Lanza excepción si falla (JSON inválido o error de API), para que el llamador
    pueda decidir si pasa al siguiente modelo de la lista de fallback.

    Args:
        time_out: Timeout en SEGUNDOS (se convierte internamente a milisegundos,
                  que es la unidad que espera el SDK google-genai).
    """
    
    response = await client.aio.models.generate_content(
        model=modelo,
        contents=[
            types.Content(
                role="user",
                parts=parts
            )
        ],
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=time_out * 1000)  # segundos -> milisegundos
        ),
    )
    
    data = _limpiar_respuesta(response.text, model=modelo)  # puede lanzar json.JSONDecodeError

    # Si los campos clave no fueron detectados (ej: la imagen no es una factura),
    # no se acepta como resultado válido: se lanza una excepción para que
    # extraer_factura pueda intentar con el siguiente modelo de la lista.
    # Se consideran "vacíos" tanto None como placeholders típicos (""/"N/A"/etc.).
    # Para "total" también se trata 0/0.0 como vacío, ya que un modelo puede devolver
    # 0.0 en vez de null cuando no encuentra el monto (confirmado en logs con
    # gemini-3.1-flash-lite en imágenes sin datos de factura).
    campos_texto_clave = ["empresa", "ruc_empresa", "fecha", "numero_factura"]
    todos_los_textos_vacios = all(_campo_vacio(data.get(campo)) for campo in campos_texto_clave)
    total_valor = data.get("total")
    total_vacio = _campo_vacio(total_valor) or total_valor in (0, 0.0)

    if todos_los_textos_vacios and total_vacio:
        
        raise CamposNoDetectadosError("campos requeridos no detectados en la imagen")

    return FacturaExtraida(**data)

async def extraer_factura(
    imagen_1: bytes,
    imagen_2: Optional[bytes] = None,
    mime_type_1: str = "image/jpeg",
    mime_type_2: str = "image/jpeg",
    time_out:int=0
    
) -> FacturaExtraida:
    """
    Extrae datos de una factura desde una o dos imágenes usando Gemini.

    Prueba los modelos definidos en GEMINI_MODELS en orden, de a uno: si el modelo
    actual falla (error de API, rate limit, JSON inválido), se intenta con el siguiente
    modelo de la lista antes de darse por vencido.

    Args:
        imagen_1: Primera imagen en bytes.
        imagen_2: Segunda imagen opcional en bytes, útil si la factura tiene 2 páginas.
        mime_type_1: Tipo MIME de la primera imagen.
        mime_type_2: Tipo MIME de la segunda imagen.

    Returns:
        FacturaExtraida: Datos extraídos de la factura con fiabilidad.

    Raises:
        ValueError: Si NINGÚN modelo de la lista devolvió JSON válido (con el mensaje
                    del ÚLTIMO modelo intentado).
        RuntimeError: Si NINGÚN modelo de la lista pudo responder (con el mensaje
                      del ÚLTIMO modelo intentado).
    """
    parts = [types.Part(text=SYSTEM_PROMPT)]

    # Agregar primera imagen
    parts.append(_crear_parte_imagen(imagen_1, mime_type_1))

    # Agregar segunda imagen si existe
    if imagen_2 is not None:
        parts.append(_crear_parte_imagen(imagen_2, mime_type_2))

    # Si se pasó un modelo explícito, se intenta primero; luego el resto de la lista
    # (sin duplicarlo si ya está incluido).
    
    modelos_a_intentar = GEMINI_MODELS

    ultimo_error: Optional[Exception] = None

    for modelo in modelos_a_intentar:
        
        try:
            return await _extraer_con_modelo(modelo, parts,time_out)

        except CamposNoDetectadosError as e:
            ultimo_error = e
            
            continue

        except json.JSONDecodeError as e:
            ultimo_error = e
            
            data_error = {
                            "proceso": 'Lector Imagenes',
                            "modelo": modelo,
                            "respuesta": f"Gemini no devolvió JSON válido con el modelo: {str(e)}"
                        }
            try:
                await registro_error(data_error)
            except Exception as err_registro:
                print(f'no se pudo registrar el error del modelo {modelo}: {err_registro}')
            continue

        except Exception as e:
            ultimo_error = e
            
            data_error = {
                            "proceso": 'Lector Imagenes',
                            "modelo": modelo,
                            "respuesta": f"Error en la API de Gemini con el modelo {modelo}: {str(e)}"
                        }
            try:
                await registro_error(data_error)
            except Exception as err_registro:
                print(f'no se pudo registrar el error del modelo {modelo}: {err_registro}')
            continue

    # Si llegamos acá, ningún modelo de la lista funcionó.
    # Se retorna/lanza el mensaje del ÚLTIMO modelo intentado.
    
    if isinstance(ultimo_error, CamposNoDetectadosError):
        # Ningún modelo pudo detectar los campos clave: no es un error de API/JSON,
        # es un resultado válido que indica que la imagen no tiene datos de factura.
        return FacturaExtraida(
            success_registro=True,
            mensaje_error="campos requeridos no detectados en la imagen",
            data_correct=False
        )

    if isinstance(ultimo_error, json.JSONDecodeError):
        msj=f"Gemini no devolvió JSON válido con ninguno de los modelos {modelos_a_intentar}.Último error ({modelos_a_intentar[-1]}): {ultimo_error} "
        return FacturaExtraida(success_registro=False, mensaje_error=msj)

    msj=f"Error al procesar la imagen con Gemini con todos los modelos {modelos_a_intentar}. Último error ({modelos_a_intentar[-1]}): {ultimo_error}"
    return FacturaExtraida(success_registro=False, mensaje_error=msj)