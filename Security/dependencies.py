"""
Adaptador para FastAPI: Depends() en lugar de decorador.
Valida JWT + Sesión activa en BD en un solo paso.
"""
from fastapi import HTTPException, Request
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from Config.settings import settings, AsyncSessionLocal
from Security.jwt_utils import AuthError, validar_token
from Models.SesionesActivas import SesionesActivas
from Common.cookie_names import ACCESS_COOKIE


async def _validar_core(request: Request, db: AsyncSession) -> dict:
    """Lógica central: valida JWT + sesión activa en BD."""
    raw_token = request.cookies.get(ACCESS_COOKIE)

    if not raw_token:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            raw_token = auth_header[7:]

    try:
        payload = validar_token(raw_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token de tipo incorrecto")

    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Token sin identificador de sesión")
    
    result = await db.execute(
        select(SesionesActivas).where(
            and_(
                SesionesActivas.SessionId == session_id,
                SesionesActivas.Activa == True,
            )
        )
    )
    sesion = result.scalars().first()
    
    if not sesion:
        raise HTTPException(status_code=401, detail="Sesión revocada o expirada")

    request.state.usuario = payload.get("sub")
    request.state.id_usuario = payload.get("user_id")
    request.state.session_id = session_id

    return payload


async def usuario_autenticado(request: Request) -> dict:
    """
    Llamada manualmente desde auth_guard() (Security/guards.py) con un
    solo argumento (request) — no pasa por el mecanismo de Depends de
    FastAPI, así que no puede recibir una sesión inyectada. Por eso
    abre su propia sesión de DB, dedicada solo a esta validación.
    """
    async with AsyncSessionLocal() as session:
        return await _validar_core(request, session)