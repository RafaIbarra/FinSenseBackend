from fastapi import Depends, Form, HTTPException, Request, Response,status,File, UploadFile
from Config.settings import get_db,settings
from sqlalchemy.ext.asyncio import AsyncSession
from Common.routers_factory import generar_router
from Integrations.groq_clasificador import disponibilidad
router_models = generar_router('/models')
@router_models.get("/groq")
async def listar(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    modelos = await disponibilidad()
    
    return {
        "status": "success",
        "empresas":modelos
    }