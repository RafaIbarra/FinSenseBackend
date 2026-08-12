from datetime import  timedelta


from fastapi import Depends, Form, HTTPException, Request, Response

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Common.routers_factory import generar_router
from Config.settings import get_db,settings
from Models.SesionesActivas import SesionesActivas
from Models.Usuarios import Usuarios

from Security.password_utils import verify_password
from Security.jwt_utils import create_token
# ─── Routers ───────────────────────────────────────────────────────────────────
_PREFIX = '/sessions'
router_sesion_public = generar_router(_PREFIX, ["Sesiones"], protegido=False)
router_sesion_protegida = generar_router(_PREFIX, ["Sesiones"])

# ─── Configuración ─────────────────────────────────────────────────────────────

_ACCESS_TTL_MINUTES = 60 * 24 * 7
_REFRESH_TTL_MINUTES = 60 * 24 * 7
_COOKIE_MAX_AGE = 60 * 60 * 24 * 7



def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    if settings.MODO_PRODUCCION:
        kwargs = {
            "httponly": True,
            "samesite": "Lax",      # mismo dominio
            "secure": True,         # obligatorio en producción con HTTPS
            "path": "/",
            "max_age": _COOKIE_MAX_AGE,
        }
        # ─── Si frontend y backend estuvieran en dominios distintos ─────────
        # kwargs = {
        #     "httponly": True,
        #     "samesite": "None",   # obligatorio para cross-site
        #     "secure": True,       # obligatorio cuando SameSite=None
        #     "path": "/",
        #     "max_age": _COOKIE_MAX_AGE,
        # }
    else:
        kwargs = {
            "httponly": True,
            "samesite": None,
            "secure": False,
            "path": "/",
            "max_age": _COOKIE_MAX_AGE,
        }

    response.set_cookie(key="access_token", value=access_token, **kwargs)
    response.set_cookie(key="refresh_token", value=refresh_token, **kwargs)

# ─── Endpoints ────────────────────────────────────────────────────────────────

@router_sesion_public.post("/login")
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

    # 2. Registrar sesión activa
    dispositivo = request.headers.get("user-agent", "unknown")
    ip_conexion = request.client.host if request.client else "unknown"

    sesion = SesionesActivas(
        UsuarioId=user.Id,
        Dispositivo=dispositivo,
        IpConexion=ip_conexion,
    )
    db.add(sesion)
    await db.commit()
    await db.refresh(sesion)

    # 3. Generar tokens
    access_token = create_token(
        str(user.UserName),str(user.Id), "access", timedelta(minutes=_ACCESS_TTL_MINUTES)
    )
    refresh_token = create_token(
        str(user.Id),str(user.Id), "refresh", timedelta(minutes=_REFRESH_TTL_MINUTES)
    )

    # 4. Setear cookies
    _set_auth_cookies(response, access_token, refresh_token)

    # 5. Responder
    return {
        "status": "success",
        "UserName": user.UserName,
        "UserId": user.Id,
        "Correo": user.Correo,
        "SesionId": sesion.Id,
    }


@router_sesion_protegida.get("/control-sesion")
async def control_sesion(request: Request):
    
    respuesta={
        'Usuario':request.state.usuario,
        'IdUsuario':request.state.id_usuario,
    }
    return respuesta