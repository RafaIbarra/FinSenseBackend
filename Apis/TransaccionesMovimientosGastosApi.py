from datetime import date
from typing import List, Optional

from fastapi import Depends, Form, HTTPException, Request,status,File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from Common.routers_factory import generar_router
from Config.settings import get_db



from Schemas.Respuestas import RespuestaProcesamientoImgFacturas
from Schemas.apis_schemas import RegistroMovimientoGastoRequest

from Repositories.empresas_repo import obtener_o_crear_empresa
from Repositories.categorias_gastos_repo import obtener_o_crear_categoria
from Repositories.conceptos_gastos_repo import obtener_o_crear_conceptos
from Repositories.etiquetas_gastos_repo import obtener_o_crear_etiquetas
from Repositories.imagenes_pendientes_repo import registrar_imagenes_pendientes
from Repositories.movimientos_gastos_repo import eliminar_movimiento, registrar
from Repositories.urls_imagenes_temporales_repo import registrar_urls_temporales
from Services.img_factura_services import procesar_imagen_factura
from Models.MovimientosGastos import TipoRegistroEnum

from Integrations.r2_storage import *

router_movimientos = generar_router('/gastos')




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


@router_movimientos.post("/extraer-clasificar")
async def extraer_clasificar(
    request: Request,
    imagenes: List[UploadFile] = File(..., description="1 o 2 imágenes de la factura (jpg, png, webp)"),
    db: AsyncSession = Depends(get_db),
):
    id_usuario = int(request.state.id_usuario)
    if len(imagenes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos 1 imagen de la factura.",
        )

    if len(imagenes) > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 2 imágenes permitidas (factura de 1 o 2 páginas).",
        )

    for imagen in imagenes:
        if not imagen.content_type or not imagen.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo '{imagen.filename}' no es una imagen válida.",
            )

    try:
        
        respuesta:Optional[RespuestaProcesamientoImgFacturas] = None
        
        imagenes_procesadas = []
        for img in imagenes:
            contenido = await img.read()
            mime = img.content_type or "image/jpeg"
            nombre = img.filename or "factura.jpg"
            imagenes_procesadas.append((contenido, mime, nombre))
        
        respuesta = await procesar_imagen_factura(imagenes=imagenes_procesadas,upload_file=True, temp_url=True,time_out_model=180)
        
        
        if not respuesta.procesamiento_correcto:
            
        
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
            "solicita_envio_pendiente": respuesta.solicita_envio_pendiente,
            "mensaje_error": respuesta.mensaje_error,
                 }
            )
        
        lista_urls=respuesta.imagenes.urls_img
        registro_urls_temporales=await registrar_urls_temporales(db,id_usuario,lista_urls)
        if not registro_urls_temporales.success_registro:
            raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                        "solicita_envio_pendiente":True,
                        "mensaje_error": registro_urls_temporales.mensaje,
                             }
                        )
        data_respuesta={
            "factura": respuesta.factura,
            "clasificacion": respuesta.clasificacion,
            "imagenes": respuesta.imagenes,
            "tipo_registro":TipoRegistroEnum.Asistido
            
        }
        return data_respuesta
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al extraer y clasificar la factura: {str(exc)}",
        )


@router_movimientos.post("/registro")
async def registro(
    request: Request,
    body: RegistroMovimientoGastoRequest,
    db: AsyncSession = Depends(get_db),
):
    id_usuario = int(request.state.id_usuario)

    #VERIFICA NUEVAMENTE QUE LA FACTURA NO TIENE ERROR
    
    factura=body.factura
    if not factura.data_correct:
                    
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=factura.mensaje_error)

    #VERIFICACION DE CONCEPTOS
    ids_conceptos=[]
    if factura.detalle:
        registros_conceptos = await obtener_o_crear_conceptos(db, factura.detalle)
        if not registros_conceptos.success_registro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=registros_conceptos.mensaje,
            )
        ids_conceptos = registros_conceptos.data_registro
    
    #VERIFICACION DE EMPRESA, SI HAY ERROR EN ESTE PROCESO SE CORTA 
    ruc=factura.ruc_empresa
    nombre_empresa=factura.empresa
    rubro=factura.rubro

    registro_empresa = await obtener_o_crear_empresa(db, nombre_empresa, ruc,rubro)
    if not registro_empresa.success_registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=registro_empresa.mensaje,
        )

    #VERIFICACION DE ETIQUETAS
    ids_etiquetas=[]
    
    etiquetas=body.clasificacion.etiquetas
    registros_etiquetas = await obtener_o_crear_etiquetas(db, etiquetas)
    if not registros_etiquetas.success_registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=registros_etiquetas.mensaje,
        )
    ids_etiquetas = registros_etiquetas.data_registro

    #VERIFICACION DE CATEGORIAS, YA TRAE LA CATEGORIA "VARIOS" DE SER NECESARIO
    nombre_categoria=body.clasificacion.categoria
    modelo_clasificador=body.clasificacion.modelo_clasificador
    registro_categoria = await obtener_o_crear_categoria(db, nombre_categoria)
    if not registro_categoria.success_registro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=registro_categoria.mensaje,
        )
    id_categoria = registro_categoria.data_registro.Id

    #LISTADO DE URLS DE IMAGENES
    imagenes=body.imagenes.urls_img
    type_url=body.imagenes.tipo_url
    try:
        #PAYLOAD PARA EL REGISTRO
        movimiento_data = {
                    "id": 0,
                    "user_id": id_usuario,
                    "total": int(factura.total),
                    "iva_diez": int(factura.iva_diez),
                    "iva_cinco": int(factura.iva_cinco),
                    "ruc": factura.ruc_empresa,
                    "id_categoria": id_categoria,
                    "nro_factura": factura.numero_factura,
                    "imagenes": imagenes,
                    "type_url":type_url,
                    "tipo_registro":body.tipo_registro ,
                    "fecha_gasto": date.fromisoformat(factura.fecha),
                    "conceptos":ids_conceptos,
                    "etiquetas":ids_etiquetas,
                    "model_img":factura.Model,
                    "model_clasificador":modelo_clasificador
                }
        
        
        registro_gasto = await registrar(db, movimiento_data)
        if registro_gasto.success_registro:
            return {'detail':'Su factura fue procesada'}
        else:
        
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=registro_gasto.mensaje)
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Error registro factura 1: {str(e)}")

@router_movimientos.post("/registro-pendiente")
async def registro_pendiente(
    request: Request,
    imagenes: List[UploadFile] = File(..., description="1 o 2 imágenes de la factura (jpg, png, webp)"),
    observacion: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    id_usuario = int(request.state.id_usuario)
    if len(imagenes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos 1 imagen de la factura.",
        )

    if len(imagenes) > 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 2 imágenes permitidas (factura de 1 o 2 páginas).",
        )

    for imagen in imagenes:
        if not imagen.content_type or not imagen.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo '{imagen.filename}' no es una imagen válida.",
            )

    try:
        
        
        
        imagenes_procesadas = []
        for img in imagenes:
            contenido = await img.read()
            mime = img.content_type or "image/jpeg"
            nombre = img.filename or "factura.jpg"
            imagenes_procesadas.append((contenido, mime, nombre))
        
        if not imagenes_procesadas:
            raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={ "No se pre procesaron las imagenes"}
                    )

        registro_pendiente=await registrar_imagenes_pendientes(db,id_usuario,imagenes_procesadas,observacion)
        
        if not registro_pendiente.success_registro:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=registro_pendiente.mensaje
                                )
        return {'detail':'Sus imagenes fueron puestas como pendientes'}
        
        # if not respuesta.procesamiento_correcto:
            
        
        

        
        
        # data_respuesta={
        #     "factura": respuesta.factura,
        #     "clasificacion": respuesta.clasificacion,
        #     "imagenes": respuesta.imagenes,
        # }
        # return data_respuesta
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al poner como pendiente: {str(exc)}",
        )

