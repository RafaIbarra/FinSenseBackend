import re


def limpiar_mensaje_error_bd(mensaje: str) -> str:
    """Limpia mensajes de excepciones de SQLAlchemy/asyncpg dejando solo la parte
    relevante (el error de PostgreSQL, con su DETAIL si existe), sin la ruta de la
    excepción de Python, el SQL ejecutado, los parámetros ni el link de referencia
    de SQLAlchemy.

    Si el mensaje no tiene el formato típico de un error de BD (por ejemplo, es una
    excepción genérica de Python), se devuelve tal cual, sin modificaciones.
    """
    if not mensaje:
        return mensaje

    texto = mensaje

    # Cortar todo desde "[SQL:" en adelante (sentencia SQL, parámetros, link de referencia)
    texto = re.split(r"\[SQL:", texto)[0]

    # Quitar el prefijo del driver/excepción, ej:
    # (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.ForeignKeyViolationError'>:
    # (psycopg2.errors.UniqueViolation)
    texto = re.sub(r"^\([\w\.]+\)\s*(<class '[^']+'>:\s*)?", "", texto)

    # Quitar espacios/saltos de línea al final y el punto final si existe
    texto = texto.strip().rstrip(".")

    return texto