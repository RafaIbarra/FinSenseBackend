import re
from Models.ErroresModelos import ErroresModelos
# Códigos HTTP / status conocidos -> tipo de error legible
_CODIGOS_ERROR = {
    400: "Solicitud Inválida",
    401: "Autenticación",
    403: "Prohibido",
    404: "Modelo No Encontrado",
    408: "Tiempo de Espera Agotado",
    429: "Límite de Tasa Excedido",
    500: "Error Interno del Servidor",
    502: "Gateway Inválido",
    503: "Servicio No Disponible",
    504: "Tiempo de Espera Agotado",
}

# Patrones para extraer el código de estado del texto de error.
# Cubre tanto "Error code: 429 - {...}" (Groq/OpenAI) como "429 RESOURCE_EXHAUSTED. {...}" (Gemini)
_PATRON_CODIGO = re.compile(
    r"(?:Error code:\s*|['\"]?code['\"]?\s*[:=]\s*)(\d{3})\b|\b(\d{3})\s+[A-Z_]{3,}\b"
)

# Patrones para errores que no traen un código HTTP explícito
_PATRONES_SIN_CODIGO = (
    (re.compile(r"unexpected keyword argument|can't be awaited|object has no attribute", re.IGNORECASE), "Error de Implementación"),
    (re.compile(r"validation error", re.IGNORECASE), "Error de Validación de Datos"),
)


def _clasificar_error(mensaje: str) -> str:
    """Clasifica un mensaje de error de un modelo/IA según su código HTTP o patrón conocido."""
    if not mensaje:
        return "Desconocido"

    match = _PATRON_CODIGO.search(mensaje)
    if match:
        codigo = int(match.group(1) or match.group(2))
        return _CODIGOS_ERROR.get(codigo, f"Error HTTP {codigo}")

    for patron, tipo in _PATRONES_SIN_CODIGO:
        if patron.search(mensaje):
            return tipo

    return "Desconocido"


def error_a_dict(error: ErroresModelos) -> dict:
    """Convierte una fila de ErroresModelos en dict, agregando la clasificación TipoError."""
    data = {columna.name: getattr(error, columna.name) for columna in error.__table__.columns}

    data["TipoError"] = _clasificar_error(data.get("RespuestaError") or "")
    return data