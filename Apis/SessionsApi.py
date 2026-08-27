from datetime import timedelta
import uuid

from fastapi import Depends, Form, HTTPException, Request, Response

from sqlalchemy import select,  and_,update
from sqlalchemy.ext.asyncio import AsyncSession

from Common.routers_factory import generar_router
from Config.settings import get_db, settings
from Models.SesionesActivas import SesionesActivas
from Models.Usuarios import Usuarios

from Security.password_utils import verify_password
from Security.jwt_utils import create_token,validar_token, AuthError
from Common.cookie_names import ACCESS_COOKIE, REFRESH_COOKIE
from Common.rate_limit_middleware import rate_limit
from Utils.error_utils import limpiar_mensaje_error_bd

# ─── Routers ───────────────────────────────────────────────────────────────────
_PREFIX = '/sessions'
router_sesion_public = generar_router(_PREFIX, ["Sesiones"], protegido=False)
router_sesion_protegida = generar_router(_PREFIX, ["Sesiones"])

# ─── Configuración ─────────────────────────────────────────────────────────────

# Navegador / dispositivos no móviles: 1 hora
_BROWSER_ACCESS_TTL_MINUTES = 60
_BROWSER_REFRESH_TTL_MINUTES = 60 * 24  # refresh token dura 1 día para renovar

# Móvil: sesión larga (30 días)
_MOBILE_ACCESS_TTL_MINUTES = 60 * 24 * 30
_MOBILE_REFRESH_TTL_MINUTES = 60 * 24 * 30

_COOKIE_MAX_AGE_BROWSER = 60 * 60  # 1 hora en segundos
_COOKIE_MAX_AGE_MOBILE = 60 * 60 * 24 * 30  # 30 días


def _es_dispositivo_movil(user_agent: str) -> bool:
    """Detecta si el user-agent corresponde a un dispositivo móvil."""
    if not user_agent:
        return False
    ua = user_agent.lower()
    mobile_keywords = [
        "mobile", "android", "iphone", "ipad", "ipod", "windows phone",
        "blackberry", "opera mini", "webos"
    ]
    return any(kw in ua for kw in mobile_keywords)


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    max_age: int,
) -> None:
    if settings.MODO_PRODUCCION:
        kwargs = {
            "httponly": True,
            "samesite": "Lax",
            "secure": True,
            "path": "/",
            "max_age": max_age,
        }
    else:
        kwargs = {
            "httponly": True,
            "samesite": "Lax",
            "secure": False,
            "path": "/",
            "max_age": max_age,
        }

    response.set_cookie(key=ACCESS_COOKIE, value=access_token, **kwargs)
    response.set_cookie(key=REFRESH_COOKIE, value=refresh_token, **kwargs)


def _clear_auth_cookies(response: Response) -> None:
    """Limpia las cookies de autenticación."""
    response.delete_cookie(key=ACCESS_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_COOKIE, path="/")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router_sesion_public.post("/login")
@rate_limit(max_requests=5, window_seconds=60)
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # 1. Autenticar usuario
    result = await db.execute(
        select(Usuarios).where(Usuarios.UserName == username)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario incorrecto")

    if not verify_password(password, user.Password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    # 2. Detectar tipo de dispositivo
    user_agent = request.headers.get("user-agent", "unknown")
    es_movil = _es_dispositivo_movil(user_agent)
    dispositivo = user_agent
    ip_conexion = request.client.host if request.client else "unknown"


    

    # 4. Crear nueva sesión activa con identificador único
    try:
        await db.execute(
                        update(SesionesActivas)
                        .where(SesionesActivas.UsuarioId == user.Id)
                        .values(Activa=False)
                    )
        await db.commit()

        session_id = str(uuid.uuid4())
        sesion = SesionesActivas(
            UsuarioId=user.Id,
            Dispositivo=dispositivo,
            IpConexion=ip_conexion,
            SessionId=session_id,  
            EsMovil=es_movil,      
            Activa=True,           
        )
        db.add(sesion)
        await db.commit()
        await db.refresh(sesion)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=limpiar_mensaje_error_bd(str(exc)))
    # 5. Definir TTL según dispositivo
    if es_movil:
        access_ttl = _MOBILE_ACCESS_TTL_MINUTES
        refresh_ttl = _MOBILE_REFRESH_TTL_MINUTES
        cookie_max_age = _COOKIE_MAX_AGE_MOBILE
    else:
        access_ttl = _BROWSER_ACCESS_TTL_MINUTES
        refresh_ttl = _BROWSER_REFRESH_TTL_MINUTES
        cookie_max_age = _COOKIE_MAX_AGE_BROWSER

    # 6. Generar tokens (incluyendo session_id en el payload para validación)
    try:
        access_token = create_token(
            subject=str(user.UserName),
            user_id=str(user.Id),
            session_id= str(session_id),
            token_type="access",
            expires_delta=timedelta(minutes=access_ttl)
            
        )
        refresh_token = create_token(
            subject=str(user.Id),
            user_id=str(user.Id),
            session_id= str(session_id),
            token_type="refresh",
            expires_delta=timedelta(minutes=refresh_ttl),
            
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    # 7. Setear cookies
    _set_auth_cookies(response, access_token, refresh_token, cookie_max_age)

    # 8. Responder
    return {
        "status": "success",
        "UserName": user.UserName,
        "UserId": user.Id,
        "Correo": user.Correo,
        "SesionId": sesion.Id,
        "Dispositivo": "Móvil" if es_movil else "Navegador/Otro",
        "ExpiraEnMinutos": access_ttl,
    }


@router_sesion_protegida.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Cierra la sesión actual y limpia las cookies."""
    # Obtener session_id del token si existe
    session_id = None
    
    if hasattr(request.state, "session_id"):
        session_id = request.state.session_id
    
    if session_id:
        await db.execute(
            update(SesionesActivas)
            .where(SesionesActivas.SessionId == session_id)
            .values(Activa=False)
        )
        await db.commit()

    _clear_auth_cookies(response)
    return {"status": "success", "detail": "Sesión cerrada correctamente"}



@router_sesion_public.post("/refresh-token")
@rate_limit(max_requests=10, window_seconds=60)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # 1. Extraer refresh_token
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if not raw_token:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            raw_token = auth_header[7:]

    if not raw_token:
        raise HTTPException(status_code=401, detail="Refresh token no proporcionado")

    # 2. Validar JWT
    try:
        payload = validar_token(raw_token, settings.SECRET_KEY, settings.JWT_ALGORITHM)
    except AuthError:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    # 3. Verificar que sea tipo refresh
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de tipo incorrecto")

    # 4. Extraer session_id y validar sesión activa en BD
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    try:
        result = await db.execute(
            select(SesionesActivas).where(
                and_(SesionesActivas.SessionId == session_id, SesionesActivas.Activa == True)
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=limpiar_mensaje_error_bd(str(exc)))
    
    sesion = result.scalars().first()
    if not sesion:
        raise HTTPException(status_code=401, detail="Sesión revocada")

    # 5. Buscar el usuario para obtener el UserName real (FIX)
    user_id = payload.get("user_id")
    result = await db.execute(select(Usuarios).where(Usuarios.Id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # 6. Determinar TTL según dispositivo
    if sesion.EsMovil:
        access_ttl = _MOBILE_ACCESS_TTL_MINUTES
        refresh_ttl = _MOBILE_REFRESH_TTL_MINUTES
        cookie_max_age = _COOKIE_MAX_AGE_MOBILE
    else:
        access_ttl = _BROWSER_ACCESS_TTL_MINUTES
        refresh_ttl = _BROWSER_REFRESH_TTL_MINUTES
        cookie_max_age = _COOKIE_MAX_AGE_BROWSER

    # 7. Generar NUEVOS tokens
    try:
        new_access = create_token(
            subject=str(user.UserName),      # FIX: username, no ID
            user_id=str(user.Id),
            token_type="access",
            expires_delta=timedelta(minutes=access_ttl),
            session_id=session_id,
        )
        new_refresh = create_token(
            subject=str(user.Id),
            user_id=str(user.Id),
            token_type="refresh",
            expires_delta=timedelta(minutes=refresh_ttl),
            session_id=session_id,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.mensaje)

    # 8. Actualizar cookies
    _set_auth_cookies(response, new_access, new_refresh, cookie_max_age)

    return {"status": "success"}


@router_sesion_protegida.get("/control-sesion")
async def control_sesion(request: Request):
    respuesta = {
        'Usuario': request.state.usuario,
        'IdUsuario': request.state.id_usuario,
    }
    return respuesta


# ─── Middleware / Dependency para validar sesión activa ───────────────────────
# Agrega esto en tu middleware de autenticación JWT o como dependency en endpoints protegidos

