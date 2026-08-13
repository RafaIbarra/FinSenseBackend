from groq import Groq
from pydantic import BaseModel
from typing import List, Optional
from Config.settings import settings
import json
GROQ_API_KEY = settings.GROQ_API_KEY
client = Groq(api_key=GROQ_API_KEY)

# Modelo recomendado para clasificación simple.
# Llama 3.1 8B es más que suficiente para esta tarea y es el más rápido/cheap.
# Si querés más calidad, usá "llama-3.3-70b-versatile".
MODEL = getattr(settings, "GROQ_MODEL", "llama-3.1-8b-instant")


class ClasificacionGasto(BaseModel):
    categoria: str
    confianza: str  # Alta, Media, Baja


# Categorías predefinidas. El modelo debe elegir UNA de estas.
CATEGORIAS = [
    "Alimentación",
    "Transporte",
    "Salud",
    "Entretenimiento",
    "Vestimenta",
    "Hogar",
    "Educación",
    "Servicios",
    "Tecnología",
    "Nafta/Combustible",
    "Mascotas",
    "Regalos",
    "Viajes",
    "Otros"
]

SYSTEM_PROMPT_CLASIFICADOR = f"""
Eres un clasificador de gastos personales. Tu trabajo es analizar una lista de conceptos de una factura y asignarle UNA sola categoría al gasto total.

CATEGORÍAS DISPONIBLES (elige EXACTAMENTE una de esta lista):
{', '.join(CATEGORIAS)}

REGLAS:
- Analiza los conceptos como un conjunto, no individualmente.
- Si la mayoría son comestibles → Alimentación.
- Si hay nafta, lubricantes, peajes → Nafta/Combustible o Transporte.
- Si son medicamentos, consultas, análisis → Salud.
- Si son películas, juegos, eventos → Entretenimiento.
- Si son ropa, zapatos, accesorios personales → Vestimenta.
- Si son limpieza, muebles, decoración → Hogar.
- Si son cursos, libros, útiles → Educación.
- Si son luz, agua, internet, teléfono → Servicios.
- Si son celulares, computadoras, software → Tecnología.
- Si no encaja en ninguna → Otros.

Responde ÚNICAMENTE con un JSON válido en este formato exacto:
{{"categoria": "NombreCategoria", "confianza": "Alta"}}

El campo "confianza" indica qué tan seguro estás:
- "Alta": los conceptos dejan muy clara la categoría.
- "Media": hay conceptos de más de una categoría, pero predomina una.
- "Baja": los conceptos son ambiguos o no dan pistas claras.

No agregues explicaciones, no uses markdown, solo el JSON.
"""


def clasificar_gasto(conceptos: List[str]) -> ClasificacionGasto:
    """
    Clasifica un gasto basándose en los conceptos extraídos de una factura.

    Args:
        conceptos: Lista de strings con los conceptos/descripciones de los artículos.
                   Ej: ["Leche Entera 1L", "Pan Integral", "Café Molido"]

    Returns:
        ClasificacionGasto: Categoría asignada y nivel de confianza.

    Raises:
        ValueError: Si la respuesta no es JSON válido.
        RuntimeError: Si falla la API de Groq.
    """
    if not conceptos:
        return ClasificacionGasto(categoria="Otros", confianza="Baja")

    # Unimos los conceptos en un texto legible
    texto_conceptos = "\n".join(f"- {c}" for c in conceptos)

    user_prompt = f"Conceptos de la factura:\n{texto_conceptos}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CLASIFICADOR},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Baja creatividad, respuesta más determinista
            max_tokens=100,   # La respuesta es corta (JSON chiquito)
            response_format={"type": "json_object"}  # Forzar JSON
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        # Validar que la categoría esté en la lista permitida
        categoria = data.get("categoria", "Otros")
        if categoria not in CATEGORIAS:
            categoria = "Otros"

        return ClasificacionGasto(
            categoria=categoria,
            confianza=data.get("confianza", "Baja")
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Groq no devolvió JSON válido. Respuesta: {raw}") from e
    except Exception as e:
        raise RuntimeError(f"Error en la API de Groq: {str(e)}") from e