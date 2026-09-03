from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.EnvioCorreos import EnvioCorreos
from Models.Usuarios import Usuarios
from Schemas.Respuestas import RespuestaFuncion
from Services.email_service import enviar_correo
from Utils.error_utils import limpiar_mensaje_error_bd


async def registro_envio_correo(db: AsyncSession, correo: dict):
    """Registra un correo a enviar.

    correo debe incluir:
    {
        "destinatario": "usuario@correo.com",
        "asunto": "Asunto del correo",
        "nombre_template": "registro_pendiente.html",
        "data": { ... },
        "context_key": "registros",
        "usuario_id": 1,  # opcional
    }
    """
    try:
        if not correo:
            return RespuestaFuncion(success_registro=False, mensaje="Datos del correo no proporcionados")

        destinatario = str(correo.get("destinatario", "")).strip()
        asunto = str(correo.get("asunto", "")).strip()
        nombre_template = str(correo.get("nombre_template", "")).strip()
        context_key = str(correo.get("context_key", "")).strip()
        usuario_id = correo.get("usuario_id")

        if not destinatario:
            return RespuestaFuncion(success_registro=False, mensaje="El destinatario es obligatorio")

        if not asunto:
            return RespuestaFuncion(success_registro=False, mensaje="El asunto es obligatorio")

        if not nombre_template:
            return RespuestaFuncion(success_registro=False, mensaje="El nombre del template es obligatorio")

        if not nombre_template.lower().endswith(".html"):
            return RespuestaFuncion(
                success_registro=False,
                mensaje="El nombre del template debe terminar en .html",
            )

        if not context_key:
            return RespuestaFuncion(success_registro=False, mensaje="El context_key es obligatorio")

        template_path = Path("Templates") / nombre_template
        if not template_path.exists():
            return RespuestaFuncion(
                success_registro=False,
                mensaje=f"No existe el template HTML: {nombre_template}",
            )

        payload = {
            "Destinatario": destinatario,
            "Asunto": asunto,
            "NombreTemplate": nombre_template,
            "Data": correo.get("data"),
            "ContextKey": context_key,
            "UsuarioId": usuario_id,
            "Procesado": False,
        }

        registro = EnvioCorreos(**payload)
        db.add(registro)
        await db.commit()
        await db.refresh(registro)

        return RespuestaFuncion(data_registro=registro)

    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def obtener_envios_pendientes(db: AsyncSession):
    try:
        result = await db.execute(
            select(EnvioCorreos).where(EnvioCorreos.Procesado.is_(False)).order_by(EnvioCorreos.FechaRegistro.asc())
        )
        return RespuestaFuncion(data_registro=result.scalars().all())
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))

async def listado_envios_correo(db: AsyncSession):
    try:
        result = await db.execute(
            select(EnvioCorreos).order_by(EnvioCorreos.FechaRegistro.asc())
        )
        return RespuestaFuncion(data_registro=result.scalars().all())
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))



async def obtener_envios_correos(db: AsyncSession):
    try:
        result = await db.execute(
            select(
                EnvioCorreos,
                Usuarios.NombreUsuario,
                Usuarios.ApellidoUsuario,
            )
            .outerjoin(Usuarios, EnvioCorreos.UsuarioId == Usuarios.Id)
            .order_by(EnvioCorreos.FechaRegistro.desc())
        )

        registros = [
            {
                "envio": envio,
                "nombre_usuario": nombre_usuario,
                "apellido_usuario": apellido_usuario,
            }
            for envio, nombre_usuario, apellido_usuario in result.all()
        ]
        return RespuestaFuncion(data_registro=registros)
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def obtener_envios_pendientes_por_asunto(db: AsyncSession, asunto: str):
    try:
        asunto = str(asunto or "").strip()
        if not asunto:
            return RespuestaFuncion(success_registro=False, mensaje="El asunto es obligatorio")

        result = await db.execute(
            select(EnvioCorreos).where(
                EnvioCorreos.Procesado.is_(False),
                EnvioCorreos.Asunto == asunto,
            ).order_by(EnvioCorreos.FechaRegistro.asc())
        )
        return RespuestaFuncion(data_registro=result.scalars().all())
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def procesar_envio_correo(db: AsyncSession, envio_id: int):
    """Procesa un registro de correo pendiente llamando a la función genérica de envío."""
    try:
        if not envio_id:
            return RespuestaFuncion(success_registro=False, mensaje="El id del correo es obligatorio")

        result = await db.execute(
            select(EnvioCorreos).where(EnvioCorreos.Id == envio_id)
        )
        registro = result.scalars().first()

        if not registro:
            return RespuestaFuncion(
                success_registro=False,
                mensaje=f"No existe un envío de correo con id {envio_id}",
            )

        data = registro.Data
        if data is None:
            registros = []
        elif isinstance(data, list):
            registros = data
        else:
            registros = [data]

        await enviar_correo(
            destinatario=registro.Destinatario,
            asunto=registro.Asunto,
            template_name=registro.NombreTemplate,
            registros=registros,
            context_key=registro.ContextKey,
        )

        registro.FechaProcesado = datetime.now()
        registro.Procesado = True

        await db.commit()
        await db.refresh(registro)

        return RespuestaFuncion()

    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
