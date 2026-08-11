"""
Adaptador para FastAPI: Depends() en lugar de decorador, porque
así es como FastAPI resuelve request/cookies/parámetros de forma nativa.
"""
from fastapi import HTTPException, Request


from Config.settings import settings
from .jwt_utils import AuthError, validar_token


# Security/dependencies.py

from fastapi import HTTPException, Request
from Config.settings import settings
from Security.jwt_utils import AuthError, validar_token


async def usuario_autenticado(request: Request) -> dict:
    """
    Extrae el access token de:
      1. Cookie 'access_token' (web)
      2. Header 'Authorization: Bearer <token>' (mobile / API clients)
    """
    raw_token = None

    # 1. Intentar cookie primero (tu flujo web actual)
    raw_token = request.cookies.get("access_token")

    # 2. Si no hay cookie, intentar header Authorization
    if not raw_token:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            raw_token = auth_header[7:]  # quita "Bearer "

    # 3. Validar
    try:
        payload = validar_token(raw_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    return payload


def requiere_permiso(permiso: str):
    """
    Fábrica de dependencias para cuando agregues permisos por rol.
    Uso:
        Depends(requiere_permiso("analisis:evaluar"))
    """
    from fastapi import Depends as _Depends

    async def checker(payload: dict = _Depends(usuario_autenticado)) -> dict:
        permisos_usuario = payload.get("permisos", [])
        if permiso not in permisos_usuario:
            raise HTTPException(status_code=403, detail=f"No tiene el permiso '{permiso}'")
        return payload

    return checker