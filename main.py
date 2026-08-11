"""
main.py
Punto de entrada de FinSense.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from Config.settings import settings, get_db
from Apis.UsersApi import router_user_public

from Apis.SessionsApi import router_sesion_protegida,router_sesion_public


# ─── Lifespan: crea tablas al iniciar (solo en DEBUG) ────────────────────────
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     if settings.DEBUG:
#         await init_db()
#         print("✅ Tablas creadas (modo DEBUG)")
#     yield
    # Aquí puedes agregar cleanup al cerrar (cerrar engine, etc.)


# ─── Instancia FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.include_router(router_user_public)
app.include_router(router_sesion_protegida)
app.include_router(router_sesion_public)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # En producción, pon tu dominio frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Prueba la conexión a PostgreSQL ejecutando SELECT 1.
    Si falla, lanza 503 Service Unavailable.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        row = result.scalar()

        return {
            "status": "ok",
            "database": "connected",
            "result": row,
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "database": "disconnected",
                "error": str(e),
            },
        )


@app.get("/info")
async def app_info():
    """Muestra configuración actual (útil para debug)."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "database_host": settings.DB_HOST,
        "database_port": settings.DB_PORT,
        "database_name": settings.DB_NAME,
    }

