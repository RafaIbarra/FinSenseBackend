from typing import Optional, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Integrations.google_ocr_client import extraer_factura
from Integrations.groq_clasificador import clasificar_gasto
from Schemas.Respuestas import RespuestaProcesamientoImgFacturas
from Schemas.r2_storage_schemas import RespuestaImagenesSubidas, TipoUrlEnum
from Schemas.integrations_schemas import FacturaExtraida,ClasificacionGasto
from Schemas.repos_schemas import RegistroEstadisticas,RegistroEstadisticaDetalle,RegistroEstadisticaImagen
from Utils.img_works import registrar_lista_imagenes
from DataTest.data import TESTS_DATA
from Models.EstadisticasModelos import OrigenEstadisticaEnum
from Models.EstadisticasModelosDetalle import TipoOperacionEnum
from Models.Usuarios import Usuarios
from Repositories.datos_modelos_repo import registro_stast

async def procesar_imagen_factura(
                                imagenes: List[Tuple[bytes, str, str,str,str]],
                                db: AsyncSession,
                                upload_file:bool=True,temp_url:bool=False,
                                time_out_model:int=120,
                                usuario_id:int=0,
                                origen:str = '',
                                ):
    
    factura_ocr: Optional[FacturaExtraida] = None
    clasificacion_groq: Optional[ClasificacionGasto] = None
    data_img:Optional[RespuestaImagenesSubidas] = None
    data_respuesta:Optional[RespuestaProcesamientoImgFacturas] = None

    imagen_1, mime_type_1, filename_1,url_1,size_1 = imagenes[0]
    imagen_2, mime_type_2, filename_2,url_2,size_2 = None, "image/jpeg", "factura.jpg","",""

    if len(imagenes) > 1:
        imagen_2, mime_type_2, filename_2,url_2,size_2 = imagenes[1]

    
    

    try:
        origen_enum = OrigenEstadisticaEnum(origen)
    except ValueError:
        return RespuestaProcesamientoImgFacturas(
            procesamiento_correcto=False,
            solicita_envio_pendiente=False,
            mensaje_error="El origen debe ser Aplicacion o Jobs",
        )

    usuario = await db.scalar(select(Usuarios).where(Usuarios.Id == usuario_id))
    if usuario is None:
        return RespuestaProcesamientoImgFacturas(
            procesamiento_correcto=False,
            solicita_envio_pendiente=False,
            mensaje_error="El usuario no existe",
        )

    factura_ocr = await extraer_factura(
                imagen_1=imagen_1,
                imagen_2=imagen_2,
                mime_type_1=mime_type_1,
                mime_type_2=mime_type_2,
                time_out=time_out_model,
            )
    
    # factura_ocr=FacturaExtraida(**TESTS_DATA['factura'])

    #ERROR EN RESPUESTA DE MODELOS
    if not factura_ocr.success_registro:
        return RespuestaProcesamientoImgFacturas(procesamiento_correcto=False,solicita_envio_pendiente=True,mensaje_error=factura_ocr.mensaje_error)

    
    
    data_img=None
    if upload_file: #SIRVE PARA SABER SI ES UNA LISTA A SUBIR A R2
        imagenes_para_subir = [(imagen_1, filename_1),]
        if imagen_2:
            imagenes_para_subir.append((imagen_2, filename_2))
        data_img=await registrar_lista_imagenes(imagenes_para_subir,temp_url)
    else:
        data_img=RespuestaImagenesSubidas(
            tipo_url=TipoUrlEnum.Procesada,
            success=True,
            urls_img=[
                {"url": url_1, "size_bytes": int(size_1)},
                *([{"url": url_2, "size_bytes": int(size_2)}] if url_2 else []),
            ],
        )
    
    #ERROR EN FORMATO DE RESPUESTA, POR FORMATO DE RESPUESTA NO SE DA LA OPCION DE SOLICITAR ENVIO PENDIENTE
    if not factura_ocr.data_correct:
        return RespuestaProcesamientoImgFacturas(procesamiento_correcto=False,solicita_envio_pendiente=False,mensaje_error=factura_ocr.mensaje_error,imagenes=data_img)

    clasificacion_groq = await clasificar_gasto(
                {
                    "empresa": factura_ocr.empresa,
                    "rubro_empresa": factura_ocr.rubro,
                    "conceptos": factura_ocr.detalle,
                },
                time_out=time_out_model,
            )
    stats_extraccion=RegistroEstadisticaDetalle(
        tipo_operacion=TipoOperacionEnum.Extraccion,
        nombre_modelo=factura_ocr.Model,
        input_tokens=factura_ocr.stats.input_tokens,
        output_tokens=factura_ocr.stats.output_tokens,
        thoughts_tokens=factura_ocr.stats.output_tokens,
        total_tokens=factura_ocr.stats.total_tokens
    )
    stats_clasifacion=RegistroEstadisticaDetalle(
            tipo_operacion=TipoOperacionEnum.Clasificacion,
            nombre_modelo=clasificacion_groq.modelo_clasificador,
            input_tokens=clasificacion_groq.stats.input_tokens,
            output_tokens=clasificacion_groq.stats.output_tokens,
            thoughts_tokens=clasificacion_groq.stats.thoughts_tokens,
            total_tokens=clasificacion_groq.stats.total_tokens
        )
        # 
    # clasificacion_groq=ClasificacionGasto(**TESTS_DATA['clasificacion'])
    
    
    # data_img=RespuestaImagenesSubidas(**TESTS_DATA['imagenes'])
    imagenes_estadisticas = []
    
    if data_img and data_img.success:
        imagenes_estadisticas = [
            RegistroEstadisticaImagen(
                url_temporal=imagen.get("url", "") if temp_url else "",
                urls_permanente=imagen.get("url", "") if not temp_url else "",
                tamano_imagen=imagen.get("size_bytes", 0),
            )
            for imagen in data_img.urls_img
        ]

    valores_stas=RegistroEstadisticas(
        usuario_id=usuario_id,
        origen=origen_enum,
        detalles=[stats_extraccion, stats_clasifacion],
        imagenes=imagenes_estadisticas,
    )
    registro_estadistica = await registro_stast(valores_reg=valores_stas)
    id_estadistica=registro_estadistica.data_registro if registro_estadistica.success_registro else 0
    # id_estadistica=0
    return RespuestaProcesamientoImgFacturas(factura=factura_ocr,clasificacion=clasificacion_groq,imagenes=data_img,id_stats=id_estadistica)

                    