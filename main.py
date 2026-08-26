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
from Apis.TransaccionesMovimientosGastosApi import router_movimientos
from Apis.CategoriasGastosApi import router_categorias
from Apis.EmpresasApi import router_empresas
from Apis.DisponibilidadModelsApi import router_models
from Apis.ListadosGastosApi import router_movimientos_listados
from Common.rate_limit_middleware import default_rate_limiter
from Common.security_headers import SecurityHeadersMiddleware

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse

# ─── Lifespan: crea tablas al iniciar (solo en DEBUG) ────────────────────────
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     if settings.DEBUG:
#         await init_db()
#         print("✅ Tablas creadas (modo DEBUG)")
#     yield
    # Aquí puedes agregar cleanup al cerrar (cerrar engine, etc.)


# ─── Instancia FastAPI ─────────────────────────────────────────────────────────
# dependencies=[Depends(default_rate_limiter)] aplica el rate limit por
# DEFECTO a TODOS los endpoints, sin tener que declarar nada en cada uno.
# Para un endpoint con límite distinto, usar el decorador @rate_limit(...)
# de Common.rate_limit_middleware (ver ejemplo en SessionsApi.py / login).
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    dependencies=[Depends(default_rate_limiter)],
)


# ─── Handlers de error globales ────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Datos de entrada inválidos"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    if settings.MODO_PRODUCCION:
        # Acá podrías loggear el error real en archivo/Sentry
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
        )
    # En desarrollo mostrá el error para debuggear
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# ─── Routers ────────────────────────────────────────────────────────────────────
app.include_router(router_user_public)
app.include_router(router_sesion_protegida)
app.include_router(router_sesion_public)
app.include_router(router_movimientos)
app.include_router(router_movimientos_listados)
app.include_router(router_categorias)
app.include_router(router_empresas)
app.include_router(router_models)


# ─── CORS ─────────────────────────────────────────────────────────────────────
origins = ['*']
if settings.MODO_PRODUCCION:
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

    # No usar assert: se elimina si Python corre con la flag -O.
    # Este check es de seguridad y no puede depender de eso.
    if not origins or "*" in origins:
        raise RuntimeError("ALLOWED_ORIGINS mal configurado en producción")


# ─── Middlewares ──────────────────────────────────────────────────────────────
# Orden de ejecución real: el ÚLTIMO agregado es el PRIMERO en ejecutarse
# (Starlette los envuelve en capas, el último add_middleware queda más "afuera").
#
# Orden de ejecución deseado por request:
#   1. HTTPSRedirect   (afuera de todo: si es HTTP, redirige y corta acá)
#   2. CORS
#   3. SecurityHeaders (más interno: aplica headers a la respuesta ya generada)
#
# El rate limit YA NO es middleware: es una dependency (default_rate_limiter,
# ver arriba en FastAPI(dependencies=[...])) que corre a nivel de cada
# endpoint individual, después de resolverse el routing.
#
# Por eso se agregan en orden INVERSO a como se ejecutan:

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

if settings.MODO_PRODUCCION:
    # ⚠️ Si la app corre detrás de un proxy/load balancer que termina TLS
    # (Nginx, Render, Railway, Cloud Run, etc.), verificar que:
    #   - el proxy envíe el header X-Forwarded-Proto: https
    #   - uvicorn/gunicorn esté configurado para confiar en ese header
    #     (ej. uvicorn --proxy-headers)
    # De lo contrario, este middleware puede generar un loop de redirects,
    # porque va a ver siempre scheme="http" aunque el cliente use HTTPS.
    app.add_middleware(HTTPSRedirectMiddleware)


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


# @app.get("/health")
# async def health_check(db: AsyncSession = Depends(get_db)):
#     """
#     Prueba la conexión a PostgreSQL ejecutando SELECT 1.
#     Si falla, lanza 503 Service Unavailable.
#     """
#     try:
#         result = await db.execute(text("SELECT 1"))
#         row = result.scalar()

#         return {
#             "status": "ok",
#             "database": "connected",
#             "result": row,
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=503,
#             detail={
#                 "status": "error",
#                 "database": "disconnected",
#                 "error": str(e),
#             },
#         )


# @app.get("/info")
# async def app_info():
#     """Muestra configuración actual (útil para debug)."""
#     if settings.MODO_PRODUCCION:
#         raise HTTPException(status_code=404)

#     return {
#         "app_name": settings.APP_NAME,
#         "version": settings.APP_VERSION,
#         "debug": settings.DEBUG,
#         "database_host": settings.DB_HOST,
#         "database_port": settings.DB_PORT,
#         "database_name": settings.DB_NAME,
#     }