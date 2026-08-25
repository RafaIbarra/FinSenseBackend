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