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
from urllib.parse import urlparse

from Models.Usuarios import Usuarios # ajustá el import según cómo se llame en tu proyecto

async def _validar_core(request: Request, db: AsyncSession, requiere_admin: bool = False) -> dict:
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
        select(SesionesActivas, Usuarios.IsAdmin)
        .join(Usuarios, Usuarios.Id == SesionesActivas.UsuarioId)  # ajustá nombres de columnas/FK
        .where(
            and_(
                SesionesActivas.SessionId == session_id,
                SesionesActivas.Activa == True,
            )
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=401, detail="Sesión revocada o expirada")

    sesion, is_admin = row

    if requiere_admin and not is_admin:
        raise HTTPException(status_code=403, detail="Requiere privilegios de administrador")

    request.state.usuario = payload.get("sub")
    request.state.id_usuario = payload.get("user_id")
    request.state.session_id = session_id
    request.state.is_admin = bool(is_admin)  # útil si en el endpoint querés usarlo después

    return payload


async def usuario_autenticado(request: Request, requiere_admin: bool = False) -> dict:
    """
    Llamada manualmente desde auth_guard() (Security/guards.py) con
    (request, requiere_admin) — no pasa por el mecanismo de Depends de
    FastAPI, así que no puede recibir una sesión inyectada. Por eso
    abre su propia sesión de DB, dedicada solo a esta validación.
    """
    async with AsyncSessionLocal() as session:
        return await _validar_core(request, session, requiere_admin=requiere_admin)