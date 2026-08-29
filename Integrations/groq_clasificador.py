from groq import AsyncGroq

from typing import Optional, Dict
from Config.settings import settings
from Repositories.errores_modelos import registro_error
from Schemas.integrations_schemas import ClasificacionGasto
import json

GROQ_API_KEY = settings.GROQ_API_KEY
client = AsyncGroq(api_key=GROQ_API_KEY)
MODELS_FALLBACK = ["llama-3.1-8b-instant", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]

MODEL_KWARGS = {
    "llama-3.1-8b-instant": {"max_tokens": 300},
    "openai/gpt-oss-20b": {"max_tokens": 600, "reasoning_effort": "none"},
    "qwen/qwen3.6-27b": {"max_tokens": 600, "reasoning_effort": "none"},
}
DEFAULT_MODEL_KWARGS = {"max_tokens": 300}

CATEGORIA_DEFAULT = "Desconocido"
ETIQUETAS_DEFAULT = ["Sin Etiquetas"]
MAX_ETIQUETAS = 5

CLASIFICACION_SYNONYMS = {
    # Variantes → Forma canónica
    "supermercados": "Supermercados",
    "super mercado": "Supermercados",
    "super mercados": "Supermercados",
    "supermercado": "Supermercados",
    "farmacias": "Farmacias",
    "farmaceutica": "Farmacias",
    "farmaceutico": "Farmacias",
    "restaurantes": "Restaurantes",
    "gastronomico": "Gastronomias",
    "gastronomicos": "Gastronomias",
    "ferreterias": "Ferreterias",
    "tecnologias": "Tecnologia",
    "indumentarias": "Indumentarias",
    "ropa": "Indumentaria",
    "educacion": "Educacion",
    "academia": "Educacion",
    "mascotas": "Mascotas",
    "mascoteria": "Mascotas",
    "petshop": "Mascotas",
    "construccion": "Construccion",
    "jugueteria": "Jugueteria",
    "juguetes": "Jugueteria",
}

ETIQUETA_SYNONYMS = {
    # Variantes → Forma canónica
    "alimentos": "Alimentacion",
    "comida": "Alimentacion",
    "comestibles": "Alimentacion",
    }






SYSTEM_PROMPT_CLASIFICADOR = f"""
Eres un clasificador de gastos personales para facturas paraguayas/latinoamericanas.

Vas a recibir:
- "empresa": el nombre de la empresa/comercio que emitió la factura.
- "info_empresa": información adicional sobre la empresa (rubro, dirección, descripción). Puede venir vacío.
- "conceptos": una lista de ítems/productos/servicios detallados en la factura. Puede venir vacía.

Tu trabajo es devolver DOS cosas:

1) "categoria": UNA sola categoría que describa a qué se dedica la EMPRESA (no los conceptos).
   - Basate primero en el nombre de la empresa. Si reconocés la empresa (por conocimiento general o porque
     el nombre es muy indicativo del rubro), asignale la categoría correspondiente.
   - Si el nombre no te da seguridad, usa "info_empresa" (si no está vacío) como apoyo para decidir.
   - Si aun así no podés determinar el rubro con razonable confianza, devolvé "Desconocido". No inventes.
   - Ejemplos de referencia (son solo ejemplos, hay muchísimos más casos posibles, generalizá el criterio):
     * Supermercados: Biggie,Stock, Super Seis, Salemma
     * Servicios Básicos: ANDE (Administración Nacional de Electricidad), ESSAP, COPACO
     * Combustible/Estaciones de servicio: Petrobras, Puma, Barcos y Rodados
     * Farmacia: Farmacenter, Punto Farma
     * Restaurante/Gastronomía, Tecnología, Ferretería, Indumentaria, Salud, Educación, etc. son
       categorías válidas si el nombre o info de la empresa lo sugiere claramente.

2) "etiquetas": entre 1 y {MAX_ETIQUETAS} etiquetas que agrupen los CONCEPTOS de la factura (los ítems comprados),
   junto con los conceptos que corresponden a cada etiqueta.
   - Analizá los conceptos y agrupalos por tipo, asignando etiquetas cortas y generales (no una por ítem).
   - Cada concepto debe quedar asignado a UNA sola etiqueta (no lo repitas en más de una).
   - Las etiquetas deben ser coherentes con la "categoria" que asignaste a la empresa: un concepto solo puede
     recibir una etiqueta que tenga sentido dentro del rubro de esa empresa. Por ejemplo, si la categoría es
     "Supermercados", no asignes una etiqueta como "Carburantes", porque un supermercado no vende combustible;
     en ese caso, revisá el concepto y usá una etiqueta que sí sea razonable para ese rubro (o una etiqueta
     genérica si no encaja en ninguna categoría típica del rubro).
   - Si "conceptos" viene vacío, devolvé exactamente [{{"etiqueta": "{ETIQUETAS_DEFAULT[0]}", "conceptos": []}}].

Responde ÚNICAMENTE con un JSON válido en este formato exacto, sin explicaciones ni markdown:
{{"categoria": "NombreCategoria", "etiquetas": [{{"etiqueta": "Etiqueta1", "conceptos": ["Concepto1", "Concepto2"]}}, {{"etiqueta": "Etiqueta2", "conceptos": ["Concepto3"]}}]}}
"""

def _canonicalizar(texto: str, mapeo: dict) -> str:
    """
    Busca coincidencia case-insensitive en el mapeo.
    Si encuentra, devuelve la forma canónica.
    Si no, devuelve el texto original con la primera letra de cada palabra en mayúscula.
    """
    clave = texto.strip().lower()
    
    if clave in mapeo:
        
        return mapeo[clave]
    # Si no está en el mapeo, al menos normalizamos el casing a Title Case
    return texto.strip().title()

async def disponibilidad():
    models = await client.models.list()
    for m in models.data:
        print(m.id)
    return models


def _construir_user_prompt(data_clasificacion: Dict) -> str:
    empresa = (data_clasificacion.get("empresa") or "").strip()
    rubro_empresa = (data_clasificacion.get("rubro_empresa") or "").strip()
    conceptos = data_clasificacion.get("conceptos") or []

    partes = [f"Empresa: {empresa if empresa else '(sin nombre de empresa)'}"]

    if rubro_empresa:
        partes.append(f"Rubro de la empresa: {rubro_empresa}")
    else:
        partes.append("Info de la empresa: (no disponible)")

    if conceptos:
        texto_conceptos = "\n".join(f"- {c}" for c in conceptos)
        partes.append(f"Conceptos de la factura:\n{texto_conceptos}")
    else:
        partes.append("Conceptos de la factura: (no disponibles)")

    return "\n\n".join(partes)


def _normalizar_respuesta(data: dict, modelo: str) -> ClasificacionGasto:
    categoria_raw = (data.get("categoria") or "").strip()
    if not categoria_raw:
        categoria = CATEGORIA_DEFAULT
    else:
        
        categoria = _canonicalizar(categoria_raw, CLASIFICACION_SYNONYMS)

    etiquetas_raw = data.get("etiquetas")
    if not isinstance(etiquetas_raw, list):
        etiquetas_raw = []

    # Normalizar cada etiqueta, agrupando sus conceptos y evitando duplicados tras la canonicalización
    etiquetas_normalizadas: list[dict] = []
    indice_por_canon: dict[str, int] = {}
    for item in etiquetas_raw:
        if isinstance(item, dict):
            etiqueta_limpia = str(item.get("etiqueta") or "").strip()
            conceptos_item = item.get("conceptos")
            if not isinstance(conceptos_item, list):
                conceptos_item = []
            conceptos_item = [str(c).strip() for c in conceptos_item if str(c).strip()]
        else:
            # Compatibilidad por si el modelo devuelve una etiqueta suelta como string
            etiqueta_limpia = str(item).strip()
            conceptos_item = []

        if not etiqueta_limpia:
            continue

        canon = _canonicalizar(etiqueta_limpia, ETIQUETA_SYNONYMS)
        clave = canon.lower()
        if clave in indice_por_canon:
            etiquetas_normalizadas[indice_por_canon[clave]]["conceptos"].extend(conceptos_item)
        else:
            indice_por_canon[clave] = len(etiquetas_normalizadas)
            etiquetas_normalizadas.append({"etiqueta": canon, "conceptos": conceptos_item})

    if not etiquetas_normalizadas:
        etiquetas = [{"etiqueta": ETIQUETAS_DEFAULT[0], "conceptos": []}]
    else:
        etiquetas = etiquetas_normalizadas[:MAX_ETIQUETAS]

    return ClasificacionGasto(
        categoria=categoria,
        etiquetas=etiquetas,
        modelo_clasificador=modelo,
    )


async def _clasificar_con_modelo(modelo: str, user_prompt: str, time_out: int) -> ClasificacionGasto:
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

    return _normalizar_respuesta(data, modelo)


async def clasificar_gasto(data_clasificacion: Dict, time_out: int) -> ClasificacionGasto:
    
    """
    Clasifica un gasto basándose en la empresa, rubro de la empresa y los conceptos
    extraídos de una factura.

    Prueba los modelos definidos en MODELS_FALLBACK en orden, de a uno: si el modelo
    actual falla (error de API, rate limit, JSON inválido), se registra el error y se
    intenta con el siguiente modelo de la lista antes de darse por vencido.

    Args:
        data_clasificacion: dict con las claves:
            - "empresa": str, nombre de la empresa.
            - "rubro_empresa": str, rubro o actividad economica de la empresa (puede venir vacío).
            - "conceptos": List[str], ítems detallados en la factura (puede venir vacío).
        time_out: timeout en segundos para la llamada a la API.

    Returns:
        CategoriaGasto: categoria de la empresa y etiquetas de los conceptos.

    Raises:
        ValueError: Si NINGÚN modelo de la lista devolvió JSON válido.
        RuntimeError: Si NINGÚN modelo de la lista pudo responder (fallas de API).
    """
    empresa = (data_clasificacion.get("empresa") or "").strip()
    conceptos = data_clasificacion.get("conceptos") or []
    

    if not empresa and not conceptos:
        return ClasificacionGasto(
            clasificacion=CATEGORIA_DEFAULT,
            etiquetas=list(ETIQUETAS_DEFAULT),
            modelo_clasificador="",
        )

    user_prompt = _construir_user_prompt(data_clasificacion)

    ultimo_error: Optional[Exception] = None

    for modelo in MODELS_FALLBACK:
        try:
            return await _clasificar_con_modelo(modelo, user_prompt, time_out)

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