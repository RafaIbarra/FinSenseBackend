from datetime import date
from typing import List, Optional

from fastapi import Depends, Form, HTTPException, Request, Response,status,File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from Common.routers_factory import generar_router
from Config.settings import get_db,settings
from Repositories.movimientos_gastos_repo import eliminar_movimiento, registrar
from Integrations.google_ocr_client import extraer_factura,FacturaExtraida
from Integrations.groq_clasificador import clasificar_gasto,ClasificacionGasto
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

@router_movimientos.post("/registro")
async def registro(
    request: Request,
    response: Response,
    imagenes: List[UploadFile] = File(..., description="1 o 2 imágenes de la factura (jpg, png, webp)"),
    id: int = Form(0),
    modelo: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra un movimiento extrayendo datos de factura desde 1 o 2 imágenes,
    y clasifica el gasto según los conceptos detectados.

    - **imagenes**: Lista de archivos de imagen. Mínimo 1, máximo 2.
      El frontend debe enviar ambos archivos con el mismo field name: `imagenes`.
      Ejemplo con FormData en JavaScript:
      ```js
      const formData = new FormData();
      formData.append("imagenes", file1);      // página 1
      formData.append("imagenes", file2);      // página 2 (opcional)
      formData.append("id", "0");
      ```
    """
    id_usuario = int(request.state.id_usuario)
    GEMINI_MODELS=[
         "gemini-3.5-flash",
         "gemini-2.5-flash",
         "gemini-3.1-flash-lite"
    ]

    # ── Validaciones de imágenes ──────────────────────────
    if len(imagenes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos 1 imagen de la factura."
        )

    if len(imagenes) > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 2 imágenes permitidas (factura de 1 o 2 páginas)."
        )

    for img in imagenes:
        if not img.content_type or not img.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo '{img.filename}' no es una imagen válida."
            )

    # ── Leer imágenes en bytes ─────────────────────────────
    bytes_1 = await imagenes[0].read()
    bytes_2 = await imagenes[1].read() if len(imagenes) > 1 else None

    mime_1 = imagenes[0].content_type or "image/jpeg"
    mime_2 = imagenes[1].content_type if len(imagenes) > 1 else "image/jpeg"

    # ── Extraer datos con Gemini (OCR) intentando hasta 3 modelos ─
    # Construir lista de modelos a probar: si el cliente envía `modelo`, probarlo primero
    if modelo and modelo in GEMINI_MODELS:
        modelos_a_probar = [modelo] + [m for m in GEMINI_MODELS if m != modelo]
    else:
        modelos_a_probar = GEMINI_MODELS.copy()

    factura: Optional[FacturaExtraida] = None
    ultimo_error: Optional[Exception] = None

    for m in modelos_a_probar[:3]:
        try:
            factura = extraer_factura(
                imagen_1=bytes_1,
                imagen_2=bytes_2,
                mime_type_1=mime_1,
                mime_type_2=mime_2,
                model=m,
            )
            # éxito
            break
        except (ValueError, RuntimeError) as e:
            ultimo_error = e
            # intentar con el siguiente modelo
            continue
        except Exception as e:
            ultimo_error = e
            continue

    if factura is None:
        # Retornar sólo el error del último intento
        if isinstance(ultimo_error, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se pudo interpretar la respuesta del OCR: {str(ultimo_error)}"
            )
        elif isinstance(ultimo_error, RuntimeError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error del servicio OCR: {str(ultimo_error)}"
            )
        else:
            # error genérico
            raise HTTPException(status_code=500, detail=str(ultimo_error))

    # ── Clasificar gasto con Groq ─────────────────────────
    clasificacion: Optional[ClasificacionGasto] = None
    error_clasificacion: Optional[str] = None

    if factura.detalle:
        try:
            clasificacion = clasificar_gasto(factura.detalle)
        except ValueError as e:
            # Gemini funcionó pero Groq devolvió basura — no rompemos todo
            error_clasificacion = f"Respuesta inválida del clasificador: {str(e)}"
        except RuntimeError as e:
            # Groq no respondió (503, rate limit, etc.) — no rompemos todo
            error_clasificacion = f"Servicio de clasificación no disponible: {str(e)}"
    else:
        error_clasificacion = "No se detectaron conceptos para clasificar."

    # ── Respuesta final ───────────────────────────────────
    respuesta = {
        "success": True,
        "message": "Factura procesada correctamente",
        "data": factura.model_dump(),
        "id_usuario": id_usuario,
        "id_form": id,
        "clasificacion": {
            "categoria": clasificacion.categoria if clasificacion else None,
            "confianza": clasificacion.confianza if clasificacion else None,
            "error": error_clasificacion
        }
    }

    # Si hubo error de clasificación, ajustamos el mensaje pero no fallamos
    if error_clasificacion:
        respuesta["message"] = "Factura procesada, pero la clasificación falló."
        respuesta["success"] = False

    return respuesta