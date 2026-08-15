from sqlalchemy import select
from Models.Empresas import Empresas
from Models.CategoriasGastos import CategoriasGastos

from datetime import date,datetime
from typing import List, Optional

from fastapi import Depends, Form, HTTPException, Request, Response,status,File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from Common.routers_factory import generar_router
from Config.settings import get_db,settings
from Repositories.movimientos_gastos_repo import eliminar_movimiento, registrar
from Integrations.google_ocr_client import extraer_factura,FacturaExtraida
from Integrations.groq_clasificador import clasificar_gasto,ClasificacionGasto
from DataTest.data import OCR_DATA

from Repositories.empresas_repo import registrar as registrar_empresa
from Repositories.categorias_gastos_repo import registrar as registrar_categoria
from Repositories.imagenes_pendientes_repo import registrar_imagenes_pendientes

from Integrations.r2_storage import *
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
    try:
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
        
        
                    
        
        # for m in modelos_a_probar[:3]:
        #     try:
                
        #         factura = extraer_factura(
        #             imagen_1=bytes_1,
        #             imagen_2=bytes_2,
        #             mime_type_1=mime_1,
        #             mime_type_2=mime_2,
        #             model=m,
        #         )
        #         # éxito
        #         break
        #     except (ValueError, RuntimeError) as e:
        #         ultimo_error = e
        #         # intentar con el siguiente modelo
        #         continue
        #     except Exception as e:
        #         ultimo_error = e
        #         continue
        error_comunicacion_modelo=False
        nombre_categoria=""
        # if factura is None:
        #     # Retornar sólo el error del último intento
        #     if isinstance(ultimo_error, ValueError):
        #         raise HTTPException(
        #             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #             detail=f"No se pudo interpretar la respuesta del OCR: {str(ultimo_error)}"
        #         )
        #     elif isinstance(ultimo_error, RuntimeError):
        #         # raise HTTPException(
        #         #     status_code=status.HTTP_502_BAD_GATEWAY,
        #         #     detail=f"Error del servicio OCR: {str(ultimo_error)}"
        #         # )
        #         error_comunicacion_modelo=True
        #     else:
        #         # error genérico
        #         error_comunicacion_modelo=True
        #         # raise HTTPException(status_code=500, detail=str(ultimo_error))
            
        # if error_comunicacion_modelo:
        #     ts = datetime.now()
        #     formateado=ts.strftime("%Y_%m_%d_T_%H_%M_%S")
        #     codigo_tarea = f'U_{id_usuario}_F_{formateado}'
            
            
        #     try:
        #         pendientes=await registrar_imagenes_pendientes(db,codigo_tarea,id_usuario,imagenes,str(ultimo_error))
                
                
        #         if pendientes.success_registro:
        #             return {'detail':'La factura no se proceso, pero se almacenaron como pendientes, recibara un correo cuando se procesen'}
        #         else:
                    
        #             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=pendientes.mensaje)

        #     except Exception as e:
        #         raise HTTPException(
        #                         status_code=status.HTTP_400_BAD_REQUEST,
        #                         detail=f"Error registro pendientes: {str(e)}"
        #                     )
        # else:

        # # # # ── Clasificar gasto con Groq ─────────────────────────
        #     clasificacion: Optional[ClasificacionGasto] = None
        #     error_clasificacion: Optional[str] = None

            
            
        #     if factura.detalle:
        #         try:
        #             clasificacion = clasificar_gasto(factura.detalle)
        #             nombre_categoria=clasificacion.categoria
        #         except ValueError as e:
                    
        #             error_clasificacion = f"Respuesta inválida del clasificador: {str(e)}"
        #             nombre_categoria="S/N"
        #         except RuntimeError as e:
                    
        #             nombre_categoria="S/N"
        #     else:
        #         nombre_categoria="Varios"

            

            

        if not error_comunicacion_modelo:

            factura = FacturaExtraida(**OCR_DATA['data'])
            clasificacion=ClasificacionGasto(**OCR_DATA['clasificacion'])
            nombre_categoria=clasificacion.categoria

            ruc=factura.ruc_empresa
            nombre_empresa=factura.empresa
            


            registro_empresa = await db.execute(
                        select(Empresas).where(Empresas.Ruc == ruc)
                    )
            empresa=registro_empresa.scalars().first()
            if not empresa:
                empresa_data = {
                        "id": 0,
                        "nombre": nombre_empresa,
                        "ruc": ruc,
                        "logo_img": "",
                    }
                
                    
                empresa=await registrar_empresa(db, empresa_data)
                if not empresa.success_registro:
                
                    raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=empresa.mensaje
                            )
                
            

            result_categoria = await db.execute(
                    select(CategoriasGastos).where(
                        CategoriasGastos.NombreCategoria == nombre_categoria,
                        CategoriasGastos.UsuarioId == id_usuario,
                    )
                )
            categoria_usuario=result_categoria.scalars().first()
            if categoria_usuario:
                id_categoria=categoria_usuario.Id
            else:
                categoria_data = {
                        "id": 0,
                        "user_id": id_usuario,
                        "nombre": nombre_categoria,
                    }
                categoria_usuario = await registrar_categoria(db, categoria_data)
                if not categoria_usuario.success_registro:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=categoria_usuario.mensaje)
                
                id_categoria=categoria_usuario.data_registro.Id
            

            try:
                movimiento_data = {
                            "id": id,
                            "user_id": id_usuario,
                            "total": int(factura.total),
                            "iva_diez": int(factura.iva_diez),
                            "iva_cinco": int(factura.iva_cinco),
                            "ruc": factura.ruc_empresa,
                            "id_categoria": id_categoria,
                            "nro_factura": factura.numero_factura,
                            "imagenes": imagenes,
                            "tipo_registro":"Automatico" ,
                            "fecha_gasto": date.fromisoformat(factura.fecha),
                        }
                
                registro_gasto = await registrar(db, movimiento_data)
                if registro_gasto.success_registro:
                    return {'detail':'Su factura fue procesada'}
                else:
                
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=registro_gasto.mensaje)
                
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Error registro factura: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Error registro factura: {str(e)}")

    