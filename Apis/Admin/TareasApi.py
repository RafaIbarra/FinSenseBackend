import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import Depends, Form, HTTPException, Request, Query, status
from Config.settings import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from Schemas.ApisResponseSchemas.datos_usuarios_response_schema import UsuarioResumenResponse
# from Repositories.imagenes_pendientes_repo import admin_listado_imagenes_pendientes
from Repositories.tasks_queries import obtener_datos_tareas
from Services.datos_tareas_pendientes_service import datos_tareas
from .router_admin import generar_router_admin

router_admin_tasks = generar_router_admin('tasks')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = BASE_DIR / "Tasks" / "procesar_imagenes_pendientes.py"
LOG_DIR = BASE_DIR/ "Tasks" / "Logs" 
LOG_DIR.mkdir(parents=True, exist_ok=True)
ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUTF8"] = "1"

@router_admin_tasks.post("/ejecutar-pendientes")
async def procesar_pendientes(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"procesar_pendientes_{timestamp}.log"
        
        with open(log_file, "w", encoding="utf-8") as f:
            subprocess.Popen(
                [sys.executable, str(SCRIPT_PATH)],
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=str(BASE_DIR),
                start_new_session=True,
                env=ENV,
            )

        return {
            "status": "lanzado",
            "detail": "El proceso se está ejecutando en segundo plano.",
            "log_file": log_file.name,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registro ejecucion: {str(e)}")

@router_admin_tasks.get("/logs")
async def listar_logs():
    """Devuelve la lista de logs disponibles, más reciente primero."""
    if not LOG_DIR.exists():
        return {"logs": []}

    archivos = sorted(
        LOG_DIR.glob("procesar_pendientes_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    logs = [
        {
            "nombre": archivo.name,
            "fecha": datetime.fromtimestamp(archivo.stat().st_mtime).isoformat(),
            "tamano_kb": round(archivo.stat().st_size / 1024, 2),
        }
        for archivo in archivos
    ]

    return {"logs": logs}


@router_admin_tasks.get("/logs/{nombre_archivo}")
async def leer_log(nombre_archivo: str):
    """Devuelve el contenido de un log puntual."""
    # Seguridad: evita path traversal (que alguien pida ../../otro_archivo)
    if "/" in nombre_archivo or "\\" in nombre_archivo or ".." in nombre_archivo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre de archivo inválido")

    log_path = LOG_DIR / nombre_archivo

    if not log_path.exists() or not log_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log no encontrado")

    contenido = log_path.read_text(encoding="utf-8", errors="replace")

    return {
        "nombre": log_path.name,
        "fecha": datetime.fromtimestamp(log_path.stat().st_mtime).isoformat(),
        "contenido": contenido,
    }

@router_admin_tasks.get("/taks-pendientes")
async def listar_tareas(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    
    try:
        datos = await obtener_datos_tareas(db)
        resumen= await datos_tareas(db)
        if not datos.success_registro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=datos.mensaje,
            )

        return resumen.data_registro
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al obtener estadísticas de modelos: {str(e)}",
        )
