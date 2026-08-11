from fastapi import  Request
from .dependencies import usuario_autenticado
async def auth_guard(request: Request):
    payload = await usuario_autenticado(request)
    usuario = payload.get("sub") or "desconocido"
    request.state.usuario = usuario
    return payload