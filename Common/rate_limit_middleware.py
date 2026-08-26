# Common/rate_limit_middleware.py
"""
Rate limiting POR ENDPOINT, implementado como dependency de FastAPI
(ya no como middleware ASGI), para poder tener un límite distinto por
ruta sin tener que declarar nada en la mayoría de los endpoints.

Comportamiento:
  - Desarrollo: NUNCA bloquea. Solo loguea una advertencia + headers.
  - Producción: bloquea con 429 al superar el límite.

Uso:
  1) DEFAULT (no hay que hacer nada): todos los endpoints quedan
     protegidos automáticamente con DEFAULT_MAX_REQUESTS /
     DEFAULT_WINDOW_SECONDS, porque la dependency se registra UNA
     sola vez a nivel de app en main.py:

         app = FastAPI(dependencies=[Depends(default_rate_limiter)])

  2) OVERRIDE puntual (ej: /login más estricto que el resto):

         @router.post("/login")
         @rate_limit(max_requests=5, window_seconds=60)
         async def login(...):
             ...

     Importante: @rate_limit(...) va DEBAJO de @router.post/@router.get
     (se aplica a la función antes de que la ruta la registre). No
     agrega una dependency nueva ni duplica el chequeo: solo marca la
     función con el límite a usar, y default_rate_limiter lo respeta.

Limitación conocida:
  El almacenamiento es en memoria (dict por proceso). Válido con 1 solo
  worker. Si se corre con varios workers/instancias, cada uno cuenta por
  separado y el límite real termina siendo max_requests * n_workers.
  Para eso hace falta un backend compartido (Redis, etc.) — fuera del
  alcance de este cambio puntual.
"""
import time
import logging
from collections import defaultdict
from typing import Callable, Optional

from fastapi import Request, Response, HTTPException

from Config.settings import settings

logger = logging.getLogger("rate_limit")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ─── Configuración por defecto (aplica a TODO endpoint sin override) ──────────
DEFAULT_MAX_REQUESTS = 200
DEFAULT_WINDOW_SECONDS = 60


# ─── Storage: (ip, path_de_ruta) -> lista de timestamps ───────────────────────
_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _get_route_path(request: Request) -> str:
    """
    Path 'template' de la ruta (ej: /sessions/login), NO la URL literal.
    Así /users/1 y /users/2 comparten el mismo bucket, en vez de crear
    uno nuevo por cada valor de path param.
    """
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


def _check_and_register(request: Request, max_requests: int, window_seconds: int) -> int:
    """
    Registra la petición actual en su bucket (ip, path) y lanza 429
    si corresponde bloquear. Devuelve el conteo actual (post-registro).
    """
    client_ip = _get_client_ip(request)
    path = _get_route_path(request)
    key = (client_ip, path)
    now = time.time()

    # Limpiar timestamps fuera de ventana
    vigentes = [ts for ts in _buckets[key] if now - ts < window_seconds]
    current_count = len(vigentes)
    vigentes.append(now)

    # Guardar o, si quedó vacío el bucket, eliminar la key (evita
    # acumular entradas de IPs viejas para siempre en memoria)
    _buckets[key] = vigentes

    if current_count >= max_requests:
        if settings.MODO_PRODUCCION:
            raise HTTPException(
                status_code=429,
                detail="Demasiadas peticiones. Intentá más tarde.",
                headers={"Retry-After": str(window_seconds)},
            )
        else:
            logger.warning(
                f"[RateLimit] ⚠️ ADVERTENCIA IP={client_ip} Path={path} — "
                f"excedió {max_requests} peticiones pero NO se bloquea (modo desarrollo)"
            )

    return current_count + 1


async def default_rate_limiter(request: Request, response: Response) -> None:
    """
    Dependency global. Se registra UNA VEZ en main.py y se ejecuta en
    TODOS los endpoints. Si el endpoint tiene @rate_limit(...), usa ese
    límite; si no, usa el default global.
    """
    route = request.scope.get("route")
    endpoint = getattr(route, "endpoint", None)
    override = getattr(endpoint, "_rate_limit_override", None)

    if override is not None:
        max_requests, window_seconds = override
    else:
        max_requests, window_seconds = DEFAULT_MAX_REQUESTS, DEFAULT_WINDOW_SECONDS

    count = _check_and_register(request, max_requests, window_seconds)

    # Headers informativos (solo se aplican si no se bloqueó / o en dev tras advertir)
    response.headers["X-Rate-Limit-Count"] = str(count)
    response.headers["X-Rate-Limit-Max"] = str(max_requests)
    if count > max_requests and not settings.MODO_PRODUCCION:
        response.headers["X-Rate-Limit-Warning"] = "true"


def rate_limit(max_requests: int, window_seconds: int) -> Callable:
    """
    Decorador para sobreescribir el límite en un endpoint puntual.
    Debe ir DEBAJO del decorador de ruta:

        @router.post("/login")
        @rate_limit(max_requests=5, window_seconds=60)
        async def login(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func._rate_limit_override = (max_requests, window_seconds)
        return func
    return decorator