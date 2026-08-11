from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Config.Settings import get_db, settings
from Models.SesionesActivas import SesionesActivas
from Models.Usuarios import Usuarios

router = APIRouter(prefix="/sesiones", tags=["Sesiones"])

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


@router.post("/login")
async def Login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Usuarios).where(Usuarios.UserName == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario incorrecto")
    
    if  not verify_password(password, user.Password):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

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

    access_token = create_token(str(user.Id), "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_token(str(user.Id), "refresh", timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))

    cookie_max_age = 60 * 60 * 24 * 7
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite=None,
        secure=False,
        path="/",
        max_age=cookie_max_age,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite=None,
        secure=False,
        path="/",
        max_age=cookie_max_age,
    )

    return {
        "status": "success",
        "UserName": user.UserName,
        "Correo": user.Correo,
        "SesionId": sesion.Id,
    }
