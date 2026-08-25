"""
Adaptador para FastAPI: Depends() en lugar de decorador.
Valida JWT + Sesión activa en BD en un solo paso.
"""
from fastapi import HTTPException, Request, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from Config.settings import settings
from Security.jwt_utils import AuthError, validar_token
from Models.SesionesActivas import SesionesActivas

# ─── AJUSTA ESTA IMPORTACIÓN A TU PROYECTO ───────────────────────────────────
# Ejemplo típico: from Config.database import AsyncSessionLocal
# Si no sabes cuál es, busca en tu proyecto donde defines:
#   AsyncSessionLocal = async_sessionmaker(...)
# ─────────────────────────────────────────────────────────────────────────────
from Config.settings import AsyncSessionLocal


async def _validar_core(request: Request, db: AsyncSession) -> dict:
    """Lógica central: valida JWT + sesión activa en BD."""
    raw_token = None

    # 1. Cookie
    raw_token = request.cookies.get("access_token")

    # 2. Header Authorization
    if not raw_token:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            raw_token = auth_header[7:]

    # 3. Validar JWT
    try:
        payload = validar_token(raw_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    # 4. Extraer session_id
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Token sin identificador de sesión")

    # 5. Validar sesión activa en BD
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

    # 6. Guardar en request.state para endpoints
    request.state.usuario = payload.get("sub")
    request.state.id_usuario = payload.get("user_id")
    request.state.session_id = session_id

    return payload


async def usuario_autenticado(
    request: Request,
    db: AsyncSession = None,  # <-- ya no usa Depends aquí por defecto
) -> dict:
    """
    Dependency para endpoints protegidos.
    Si FastAPI inyecta la sesión (uso normal con Depends), la usa.
    Si se llama manualmente (middleware, etc.), crea una sesión al vuelo.
    """
    if isinstance(db, AsyncSession):
        return await _validar_core(request, db)

    # Fallback: crear sesión manualmente para uso fuera de endpoints
    async with AsyncSessionLocal() as session:
        return await _validar_core(request, session)