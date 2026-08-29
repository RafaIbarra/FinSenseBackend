from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from Config.settings import settings
# ── Configuración ──────────────────────────────────────────────
# Ajusta estos valores según tu entorno (mejor en variables de entorno)
EMAIL_CONF = ConnectionConfig(
    MAIL_USERNAME=settings.DIR_EMAIL,
    MAIL_PASSWORD=settings.PASS_EMAIL,
    MAIL_FROM=settings.DIR_EMAIL,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER="./Templates",  # Ruta a tus plantillas
)


class RegistroPendienteData:
    """DTO para cada fila de datos que va al correo."""
    def __init__(self, codigo_tarea: str, id_reg: int, fecha_hora_procesado: str):
        self.codigo_tarea = codigo_tarea
        self.id_reg = id_reg
        self.fecha_hora_procesado = fecha_hora_procesado




async def enviar_correo_registro_pendiente(
    destinatario: EmailStr,
    asunto: str,
    registros: List[RegistroPendienteData],
) -> None:
    """
    Envía un correo HTML usando la plantilla 'registro_pendiente.html'.
    
    Args:
        destinatario: Correo electrónico del destinatario.
        asunto: Asunto del correo.
        registros: Lista de objetos con los datos a renderizar en la tabla.
    """
    # Prepara el cuerpo con los datos para Jinja2
    template_body = {
        "registros": [
            {
                "codigo_tarea": r.codigo_tarea,
                "id_reg": r.id_reg,
                "fecha_hora_procesado": r.fecha_hora_procesado,
            }
            for r in registros
        ]
    }

    message = MessageSchema(
        subject=asunto,
        recipients=[destinatario],
        template_body=template_body,
        subtype="html",
    )

    fm = FastMail(EMAIL_CONF)
    await fm.send_message(message, template_name="registro_pendiente.html")

class UrlsTempEliminadosData:
    """DTO para cada fila de datos que va al correo."""
    def __init__(self, nombre_apellido: str, url: str, fecha_hora_registro: str,fecha_hora_eliminado:str):
        self.nombre_apellido = nombre_apellido
        self.url = url
        self.fecha_hora_registro = fecha_hora_registro
        self.fecha_hora_eliminacion = fecha_hora_eliminado




async def enviar_correo_urls_eliminadas(
    destinatario: EmailStr,
    asunto: str,
    registros: List[UrlsTempEliminadosData],
) -> None:
    """
    Envía un correo HTML usando la plantilla 'registro_pendiente.html'.
    
    Args:
        destinatario: Correo electrónico del destinatario.
        asunto: Asunto del correo.
        registros: Lista de objetos con los datos a renderizar en la tabla.
    """
    # Prepara el cuerpo con los datos para Jinja2
    template_body = {
        "registros": [
            {
                "Nombre y Apellido Usuario": r.nombre_apellido,
                "Url": r.url,
                "Fecha Registro": r.fecha_hora_registro,
                "Fecha Eliminacion":r.fecha_hora_eliminacion
            }
            for r in registros
        ]
    }

    message = MessageSchema(
        subject=asunto,
        recipients=[destinatario],
        template_body=template_body,
        subtype="html",
    )

    fm = FastMail(EMAIL_CONF)
    await fm.send_message(message, template_name="urls_temp_eliminadas.html")


# ── Función genérica ────────────────────────────────────────────
async def enviar_correo(
    destinatario: EmailStr,
    asunto: str,
    template_name: str,
    registros: List[dict],
    context_key: str = "registros",
    extra_context: dict | None = None,
) -> None:
    """
    Envía un correo HTML genérico usando cualquier plantilla y cualquier data.

    A diferencia de las funciones específicas (enviar_correo_registro_pendiente,
    enviar_correo_urls_eliminadas), esta función no depende de un DTO fijo:
    recibe la lista de filas ya como diccionarios (las claves deben coincidir
    con lo que espera la plantilla Jinja2) y el nombre del template a usar.

    Args:
        destinatario: Correo electrónico del destinatario.
        asunto: Asunto del correo.
        template_name: Nombre del archivo .html dentro de TEMPLATE_FOLDER
            (ej: "registro_pendiente.html").
        registros: Lista de diccionarios con los datos a renderizar en la
            tabla. Cada dict representa una fila, con las claves que la
            plantilla espera (ej: {"codigo_tarea": ..., "id_reg": ...}).
        context_key: Nombre de la variable dentro del template_body que
            contendrá la lista de registros (por defecto "registros").
        extra_context: Diccionario opcional con variables adicionales a
            pasar al template (ej: {"titulo": "Reporte semanal"}).

    Ejemplo:
        await enviar_correo(
            destinatario="user@mail.com",
            asunto="Registros pendientes",
            template_name="registro_pendiente.html",
            registros=[
                {"codigo_tarea": "T1", "id_reg": 1, "fecha_hora_procesado": "2026-08-28"},
            ],
        )
    """
    template_body = {context_key: registros}
    if extra_context:
        template_body.update(extra_context)

    message = MessageSchema(
        subject=asunto,
        recipients=[destinatario],
        template_body=template_body,
        subtype="html",
    )

    fm = FastMail(EMAIL_CONF)
    await fm.send_message(message, template_name=template_name)