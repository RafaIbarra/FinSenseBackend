from google import genai
from google.genai import types
import json
from pydantic import BaseModel
from typing import List, Optional, Union
from Config.settings import settings

GEMINI_API_KEY = settings.GEMINI_API_KEY
client = genai.Client(api_key=GEMINI_API_KEY)

# Modelo recomendado para OCR rápido y barato
MODEL = "gemini-3.5-flash"

# ── Schemas ───────────────────────────────────────────────
class FacturaExtraida(BaseModel):
    empresa: Optional[str] = None
    ruc_empresa: Optional[str] = None
    fecha: Optional[str] = None
    numero_factura: Optional[str] = None
    total: Optional[float] = None
    iva_diez: Optional[float] = None
    iva_cinco: Optional[float] = None
    fiabilidad: str = "Malo"  # Excelente, Bueno, Malo


# ── Prompt optimizado ─────────────────────────────────────
SYSTEM_PROMPT = """
Eres un extractor experto de datos de facturas. Analiza la imagen y devuelve ÚNICAMENTE un JSON válido.

ESTRUCTURA DE RESPUESTA:
{
  "empresa": "nombre del vendedor/empresa",
  "ruc_empresa": "4545454-4",
  "fecha": "YYYY-MM-DD",
  "numero_factura": "001-001-0000001",
  "total": 123.45,
  "iva_diez": 55.00,
  "iva_cinco": 11.00,
  "fiabilidad": "Excelente"
}

INSTRUCCIONES DE DETECCIÓN POR CAMPO:

1. EMPRESA:
   - Puede que no figure etiqueta como "Empresa" o "Razón Social".
   - Generalmente está en la parte SUPERIOR de la factura, en letras MÁS GRANDES que el resto del texto.
   - Busca el nombre comercial más prominente, usualmente en negrita o tamaño mayor.
   - Si hay varios nombres, prioriza el del vendedor/emisor (no el del cliente).

2. RUC_EMPRESA:
   - Busca etiquetas como: RUC, Nº RUC, Nro. RUC, Numero RUC, R.U.C., N° RUC, RUC Nº.
   - El formato suele ser numérico, a veces con guiones (ej: 1234567-8).
   - Extrae SOLO el número, sin la etiqueta.

3. FECHA:
   - Busca etiquetas como: Fecha, Fecha de Inicio, Fecha Factura, Fecha Emisión, Fecha de Emisión, Fec., Emisión.
   - Formato de salida SIEMPRE: YYYY-MM-DD.
   - Si la fecha está en formato DD/MM/YYYY o similar, conviértela.

4. NUMERO_FACTURA:
   - Busca etiquetas como: Nro Factura, Nº Factura, Nro. Factura, Factura Nº, No. Factura, N° de Factura.
   - Si no tiene etiqueta clara, busca un número con formato de factura: XXX-XXX-XXXXXXX (tres grupos separados por guiones).
   - Ejemplo: 001-001-0001234

5. TOTAL:
   - Busca etiquetas como: Total, Total a Pagar, Total General, Importe Total, Total Gs., Total $, Total USD.
   - Extrae el valor numérico SIN símbolo de moneda.
   - Prioriza el total FINAL (el último/más grande), no subtotales.

6. IVA_DIEZ (IVA 10%):
   - Busca etiquetas como: IVA 10%, IVA 10, I.V.A. 10%, Impuesto 10%, IVA Diez, IVA 10% Liquidación.
   - Extrae el monto numérico correspondiente al IVA al 10%.
   - Si no aparece, devuelve null.

7. IVA_CINCO (IVA 5%):
   - Busca etiquetas como: IVA 5%, IVA 5, I.V.A. 5%, Impuesto 5%, IVA Cinco, IVA 5% Liquidación.
   - Extrae el monto numérico correspondiente al IVA al 5%.
   - Si no aparece, devuelve null.

8. FIABILIDAD (campo obligatorio):
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
- Si no encuentras un campo, usa null (no omitas la clave).
- Los valores numéricos deben ser números (float o int), NUNCA strings con símbolos.
- La fecha SIEMPRE en formato ISO: YYYY-MM-DD.
- Responde SOLO con el JSON, sin markdown, sin explicaciones, sin texto adicional.
"""


def _limpiar_respuesta(raw_text: str) -> dict:
    """Limpia la respuesta de Gemini removiendo markdown y parseando JSON."""
    raw_text = raw_text.strip()
    raw_text = raw_text.removeprefix("```json").removeprefix("```")
    raw_text = raw_text.removesuffix("```").strip()
    return json.loads(raw_text)


def _crear_parte_imagen(image_bytes: bytes, mime_type: str = "image/jpeg") -> types.Part:
    """Crea un Part de Gemini a partir de bytes."""
    return types.Part(
        inline_data=types.Blob(
            mime_type=mime_type,
            data=image_bytes
        )
    )


def extraer_factura(
    imagen_1: bytes,
    imagen_2: Optional[bytes] = None,
    mime_type_1: str = "image/jpeg",
    mime_type_2: str = "image/jpeg"
) -> FacturaExtraida:
    """
    Extrae datos de una factura desde una o dos imágenes usando Gemini.

    Args:
        imagen_1: Primera imagen en bytes.
        imagen_2: Segunda imagen opcional en bytes, útil si la factura tiene 2 páginas.
        mime_type_1: Tipo MIME de la primera imagen.
        mime_type_2: Tipo MIME de la segunda imagen.

    Returns:
        FacturaExtraida: Datos extraídos de la factura con fiabilidad.

    Raises:
        ValueError: Si Gemini no devuelve JSON válido.
        RuntimeError: Si ocurre un error en la API de Gemini.
    """
    parts = [types.Part(text=SYSTEM_PROMPT)]

    # Agregar primera imagen
    parts.append(_crear_parte_imagen(imagen_1, mime_type_1))

    # Agregar segunda imagen si existe
    if imagen_2 is not None:
        parts.append(_crear_parte_imagen(imagen_2, mime_type_2))

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=parts
                )
            ]
        )

        data = _limpiar_respuesta(response.text)
        return FacturaExtraida(**data)

    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini no devolvió JSON válido. Respuesta cruda: {response.text}") from e
    except Exception as e:
        raise RuntimeError(f"Error al procesar la imagen con Gemini: {str(e)}") from e