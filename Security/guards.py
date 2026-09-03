from fastapi import  Request
from .dependencies import usuario_autenticado
def auth_guard(requiere_admin: bool = False):
    async def _guard(request: Request):
        payload = await usuario_autenticado(request, requiere_admin=requiere_admin)
        usuario = payload.get("sub") or "desconocido"
        id_usuario = payload.get("user_id") or "0"
        request.state.usuario = usuario
        request.state.id_usuario = id_usuario
        return payload
    return _guard