from fastapi import  Request
from .dependencies import usuario_autenticado
async def auth_guard(request: Request):
    payload = await usuario_autenticado(request)
    usuario = payload.get("sub") or "desconocido"
    id_usuario = payload.get("user_id") or "0"
    request.state.usuario = usuario
    request.state.id_usuario = id_usuario
    return payload