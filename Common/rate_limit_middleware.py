"""
Rate limiting con 'limits' (MovingWindowRateLimiter).
  - Desarrollo: NUNCA bloquea. Loguea advertencia + headers.
  - Producción: bloquea con 429 cuando excede.
  - Storage en memoria. Para escalar: cambiar MemoryStorage por RedisStorage.
"""
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, HTTPException
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from Config.settings import settings

# print(f"🚀 Rate limiter cargado. MODO_PRODUCCION={settings.MODO_PRODUCCION}")

# ─── Configuración por defecto ────────────────────────────────────────────────
DEFAULT_MAX_REQUESTS = 200
DEFAULT_WINDOW_SECONDS = 60

# ─── Motor de limits ──────────────────────────────────────────────────────────
_storage = MemoryStorage()
_limiter = MovingWindowRateLimiter(_storage)

# ─── Contador auxiliar para headers/logs (sliding window manual) ─────────────
_requests: dict[tuple[str, str, int], list[float]] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _get_route_path(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


def _build_limit_str(max_requests: int, window_seconds: int) -> str:
    """Construye string válido para limits.parse()."""
    return f"{max_requests} per {window_seconds} seconds"


async def default_rate_limiter(request: Request, response: Response) -> None:
    client_ip = _get_client_ip(request)
    path = _get_route_path(request)
    key = f"{client_ip}:{path}"

    # 1. Detectar si el endpoint tiene @rate_limit(...)
    route = request.scope.get("route")
    endpoint = getattr(route, "endpoint", None)
    override = getattr(endpoint, "_rate_limit_override", None)

    if override is not None:
        max_requests, window_seconds = override
    else:
        max_requests, window_seconds = DEFAULT_MAX_REQUESTS, DEFAULT_WINDOW_SECONDS

    limit_str = _build_limit_str(max_requests, window_seconds)
    parsed = parse(limit_str)

    # 2. Contador casero para headers (sliding window real)
    now = time.time()
    dict_key = (client_ip, path, window_seconds)
    _requests[dict_key] = [
        ts for ts in _requests[dict_key]
        if now - ts < window_seconds
    ]
    _requests[dict_key].append(now)
    count = len(_requests[dict_key])

    # 3. Verificar con limits
    permitido = _limiter.hit(parsed, key)

    # print(f"[RL] IP={client_ip} | Path={path} | count={count}/{max_requests} | limits_hit={permitido} | window={window_seconds}s")

    if not permitido:
        if settings.MODO_PRODUCCION:
            print(f"[RL] 🚫 BLOQUEADO {key}")
            raise HTTPException(
                status_code=429,
                detail="Demasiadas peticiones.",
                headers={"Retry-After": str(window_seconds)},
            )
        else:
            print(f"[RL] ⚠️ ADVERTENCIA: {key} excedió {limit_str}")

    # 4. Headers informativos
    response.headers["X-Rate-Limit-Count"] = str(count)
    response.headers["X-Rate-Limit-Max"] = str(max_requests)
    if count > max_requests and not settings.MODO_PRODUCCION:
        response.headers["X-Rate-Limit-Warning"] = "true"


def rate_limit(max_requests: int, window_seconds: int) -> Callable:
    """
    Decorador para sobreescribir el límite en un endpoint puntual.
    Va DEBAJO del decorador de ruta:

        @router.post("/login")
        @rate_limit(max_requests=5, window_seconds=60)
        async def login(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func._rate_limit_override = (max_requests, window_seconds)
        return func
    return decorator