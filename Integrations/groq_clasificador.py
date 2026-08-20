from groq import AsyncGroq
from pydantic import BaseModel
from typing import List, Optional
from Config.settings import settings
from Repositories.errores_modelos import registro_error
import json
GROQ_API_KEY = settings.GROQ_API_KEY
client = AsyncGroq(api_key=GROQ_API_KEY)
MODELS_FALLBACK =["llama-3.1-8b-instant", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]

MODEL_KWARGS = {
    "llama-3.1-8b-instant": {"max_tokens": 100},
    "openai/gpt-oss-20b": {"max_tokens": 600, "reasoning_effort": "low"},
    "qwen/qwen3.6-27b": {"max_tokens": 600, "reasoning_effort": "low"},
}
DEFAULT_MODEL_KWARGS = {"max_tokens": 300}

class ClasificacionGasto(BaseModel):
    categoria: str
    confianza: str  # Alta, Media, Baja
    modelo_clasificador:str


# Categorías predefinidas. El modelo debe elegir UNA de estas.
CATEGORIAS = [
    "Alimentacion",
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
- Si la mayoría son comestibles → Alimentacion.
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
async def disponibilidad():
    
    models = await client.models.list()

    for m in models.data:
        print(m.id)
    return models

async def _clasificar_con_modelo(modelo: str, user_prompt: str,time_out:int) -> ClasificacionGasto:
    """
    Intenta clasificar el gasto usando un modelo específico.
    Lanza excepción si falla (JSON inválido o error de API), para que el llamador
    pueda decidir si pasa al siguiente modelo de la lista de fallback.
    """
    extra_kwargs = MODEL_KWARGS.get(modelo, DEFAULT_MODEL_KWARGS)

    response = await client.chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_CLASIFICADOR},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,  # Baja creatividad, respuesta más determinista
        response_format={"type": "json_object"},  # Forzar JSON
        timeout=time_out,
        **extra_kwargs,
    )

    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)  # puede lanzar json.JSONDecodeError

    # Validar que la categoría esté en la lista permitida
    categoria = data.get("categoria", "Otros")
    if categoria not in CATEGORIAS:
        categoria = "Otros"

    return ClasificacionGasto(
        categoria=categoria,
        confianza=data.get("confianza", "Baja"),
        modelo_clasificador=modelo

    )


async def clasificar_gasto(conceptos: List[str],time_out:int) -> ClasificacionGasto:
    """
    Clasifica un gasto basándose en los conceptos extraídos de una factura.

    Prueba los modelos definidos en MODELS_FALLBACK en orden, de a uno: si el modelo
    actual falla (error de API, rate limit, JSON inválido), se registra el error y se
    intenta con el siguiente modelo de la lista antes de darse por vencido.

    Args:
        conceptos: Lista de strings con los conceptos/descripciones de los artículos.
                   Ej: ["Leche Entera 1L", "Pan Integral", "Café Molido"]

    Returns:
        ClasificacionGasto: Categoría asignada y nivel de confianza.

    Raises:
        ValueError: Si NINGÚN modelo de la lista devolvió JSON válido.
        RuntimeError: Si NINGÚN modelo de la lista pudo responder (fallas de API).
    """
    if not conceptos:
        return ClasificacionGasto(categoria="Otros", confianza="Baja",modelo_clasificador="")
    
    # Unimos los conceptos en un texto legible
    texto_conceptos = "\n".join(f"- {c}" for c in conceptos)

    user_prompt = f"Conceptos de la factura:\n{texto_conceptos}"

    ultimo_error: Optional[Exception] = None

    for modelo in MODELS_FALLBACK:
        try:
            return await _clasificar_con_modelo(modelo, user_prompt,time_out)

        except json.JSONDecodeError as e:
            ultimo_error = e
            data_error = {
                "proceso": 'Clasificador',
                "modelo": modelo,
                "respuesta": f"Groq no devolvió JSON válido con el modelo {modelo}: {str(e)}"
            }
            await registro_error(data_error)
            # Intentar con el siguiente modelo de la lista
            continue

        except Exception as e:
            ultimo_error = e
            data_error = {
                "proceso": 'Clasificador',
                "modelo": modelo,
                "respuesta": f"Error en la API de Groq con el modelo {modelo}: {str(e)}"
            }
            await registro_error(data_error)
            # Intentar con el siguiente modelo de la lista
            continue

    # Si llegamos acá, ningún modelo de la lista funcionó
    if isinstance(ultimo_error, json.JSONDecodeError):
        raise ValueError(
            f"Groq no devolvió JSON válido con ninguno de los modelos {MODELS_FALLBACK}: {ultimo_error}"
        ) from ultimo_error
    raise RuntimeError(
        f"Error en la API de Groq con todos los modelos {MODELS_FALLBACK}: {ultimo_error}"
    ) from ultimo_error