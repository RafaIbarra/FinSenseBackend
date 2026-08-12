from datetime import date

from fastapi import Depends, Form, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from Common.routers_factory import generar_router
from Config.settings import get_db,settings
from Repositories.movimientos_gastos_repo import eliminar_movimiento, registrar

router_movimientos = generar_router('/gastos')

@router_movimientos.post("/registro-manual")
async def registro_manual(
    request: Request,
    response: Response,
    id: int = Form(0),
    total: int = Form(...),
    iva_diez: int = Form(...),
    iva_cinco: int = Form(...),
    ruc: str = Form(...),
    id_categoria: int = Form(...),
    nro_factura: str | None = Form(None),
    fecha_gasto: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    id_usuario = int(request.state.id_usuario)
    
    tipo_registro = 'Manual'
    imagenes = []

    try:
        fecha_gasto_parsed = date.fromisoformat(fecha_gasto)

        movimiento_data = {
            "id": id,
            "user_id": id_usuario,
            "total": total,
            "iva_diez": iva_diez,
            "iva_cinco": iva_cinco,
            "ruc": ruc,
            "id_categoria": id_categoria,
            "nro_factura": nro_factura,
            "imagenes": imagenes,
            "tipo_registro": tipo_registro,
            "fecha_gasto": fecha_gasto_parsed,
        }

        resultado = await registrar(db, movimiento_data)
        if isinstance(resultado, dict) and resultado.get("error"):
            raise HTTPException(status_code=400, detail=resultado["error"])

        return {
            "status": "success",
            "id": resultado.Id,
            "user_id": resultado.UsuarioId,
            "total": resultado.TotalGasto,
            "iva_diez": resultado.IvaDiez,
            "iva_cinco": resultado.IvaCinco,
            "fecha_gasto": str(resultado.FechaGasto),
            "tipo_registro": resultado.TipoRegistro.value if hasattr(resultado.TipoRegistro, 'value') else str(resultado.TipoRegistro),
            "categoria_id": resultado.CategoriaId,
            "empresa_id": resultado.EmpresaId,
            "nro_factura": resultado.NumeroFactura,
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="fecha_gasto debe tener formato YYYY-MM-DD")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar el movimiento: {e}")


@router_movimientos.post("/eliminar")
async def eliminar(
    request: Request,
    id: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    usuario_id = int(request.state.id_usuario)
    resultado = await eliminar_movimiento(db, id, usuario_id)

    if isinstance(resultado, dict) and resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return resultado