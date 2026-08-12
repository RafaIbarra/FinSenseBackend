"""
alembic/env.py
Configuración de Alembic para migraciones asíncronas con FastAPI.
"""

import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# ─── 1. Asegurar que Python encuentre tus módulos ────────────────────────────
# Sube un nivel desde alembic/ hasta la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# ─── 2. Importar Settings y TUS MODELOS ─────────────────────────────────────
# Esto es CRÍTICO: sin importar los modelos, Alembic no sabe qué tablas existen
from Config.settings import settings, Base
import Models  # Ejecuta Models/__init__.py que registra Usuario y SesionActiva

# ─── 3. Configuración de Alembic ─────────────────────────────────────────────
config = context.config

# Lee logging de alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos donde están tus tablas (viene de declarative_base() en Settings.py)
target_metadata = Base.metadata

# Sobreescribe la URL con la de tu .env (más seguro que hardcodear en alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# ─── 4. Funciones de migración (NO TOCAR) ───────────────────────────────────
def run_migrations_offline() -> None:
    """Ejecuta migraciones sin conectarse a la DB (genera SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Wrapper síncrono que Alembic necesita."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Ejecuta migraciones conectándose a la DB."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())