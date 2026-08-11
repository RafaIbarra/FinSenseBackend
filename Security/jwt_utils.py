from dataclasses import dataclass
import jwt
from datetime import datetime, timedelta
from Config.settings import settings

@dataclass
class AuthError(Exception):
    status_code: int
    mensaje: str


def validar_token(raw_token: str, secret_key: str, algoritmo: str = "HS256") -> dict:
    """
    Valida firma, expiración y tipo de token (equivalente a
    JWTAuthentication.get_validated_token() de simplejwt, sin ORM).

    Devuelve el payload decodificado (user_id, username, exp, token_type, jti, ...).
    Lanza AuthError si algo falla.
    """
    if not raw_token:
        raise AuthError(401, "Token no proporcionado")

    try:
        payload = jwt.decode(raw_token, secret_key, algorithms=[algoritmo])
    except jwt.ExpiredSignatureError as e:
        raise AuthError(401, f"Error de token: {e}")
    except jwt.InvalidTokenError as e:
        raise AuthError(401, f"Token inválido: {e}")
    except Exception as e:
        raise AuthError(500, f"Error de validación: {e}")
    
    if payload.get("type") != "access":
        raise AuthError(401, "Token inválido: tipo de token incorrecto")

    return payload

def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    try:
        now = datetime.utcnow()
        payload = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    except Exception as e:
        raise AuthError(500, f"Error de creacion token: {e}")