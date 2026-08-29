"""
database.py
Configuración de conexión asíncrona a PostgreSQL para FinSense.
"""

import os
import sys
from pathlib import Path
from functools import lru_cache
from typing import AsyncGenerator

from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# ─── Rutas del proyecto ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(os.path.join(BASE_DIR, 'backends'))


# ─── Settings con pydantic-settings ────────────────────────────────────────────
class Settings(BaseSettings):
    APP_NAME: str = "FinSense"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str
    DEBUG: bool = False
    MODO_PRODUCCION: bool

    DB_USER: str
    DB_PASS: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str

    GEMINI_API_KEY:str
    GROQ_API_KEY:str
    JWT_ALGORITHM:str="HS256"

    R2_ACCOUNT_ID:str
    R2_ACCESS_KEY_ID:str
    R2_SECRET_ACCESS_KEY:str
    R2_ENDPOINT_URL:str

    R2_BUCKET_GASTOS:str
    R2_PUBLIC_URL_GASTOS:str

    R2_BUCKET_EMPRESAS:str
    R2_PUBLIC_URL_EMPRESAS:str

    R2_BUCKET_TEMPORALES:str
    R2_PUBLIC_URL_TEMPORALES :str

    MAIL_ADMIN:str
    DIR_EMAIL:str
    PASS_EMAIL:str
    ALLOWED_ORIGINS:str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = BASE_DIR.parent / 'BackendConfig' / '.env'
        env_file_encoding = 'utf-8'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# ─── SQLAlchemy Async ──────────────────────────────────────────────────────────
async_engine = create_async_engine(
    settings.DATABASE_URL,
    # echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


# ─── Dependency para FastAPI (CORREGIDO) ─────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency asíncrona para inyectar sesiones de DB en los routers.
    Uso:
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ─── Utilidades para crear/eliminar tablas (solo desarrollo) ─────────────────
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)