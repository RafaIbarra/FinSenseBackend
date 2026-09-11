from typing import Optional, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Integrations.google_ocr_client import extraer_factura
from Integrations.groq_clasificador import clasificar_gasto
from Schemas.Respuestas import RespuestaProcesamientoImgFacturas
from Schemas.r2_storage_schemas import RespuestaImagenesSubidas
from Schemas.integrations_schemas import FacturaExtraida,ClasificacionGasto
from Utils.img_works import registrar_lista_imagenes
from DataTest.data import TESTS_DATA
from Models.EstadisticasModelos import OrigenEstadisticaEnum
from Models.Usuarios import Usuarios


async def procesar_imagen_factura(
                                imagenes: List[Tuple[bytes, str, str]],
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

    imagen_1, mime_type_1, filename_1 = imagenes[0]
    imagen_2, mime_type_2, filename_2 = None, "image/jpeg", "factura.jpg"

    if len(imagenes) > 1:
        imagen_2, mime_type_2, filename_2 = imagenes[1]

    
    size_img_uno = len(imagen_1)
    size_img_dos = len(imagen_2) if imagen_2 else 0

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
    print(factura_ocr)
    # factura_ocr=FacturaExtraida(**TESTS_DATA['factura'])

    #ERROR EN RESPUESTA DE MODELOS
    if not factura_ocr.success_registro:
        return RespuestaProcesamientoImgFacturas(procesamiento_correcto=False,solicita_envio_pendiente=True,mensaje_error=factura_ocr.mensaje_error)

    
    
    data_img=None
    if upload_file:
        imagenes_para_subir = [(imagen_1, filename_1),]
        if imagen_2:
            imagenes_para_subir.append((imagen_2, filename_2))
        data_img=await registrar_lista_imagenes(imagenes_para_subir,temp_url)
        
    print(data_img)
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
    
    # clasificacion_groq=ClasificacionGasto(**TESTS_DATA['clasificacion'])
    
    
    # data_img=RespuestaImagenesSubidas(**TESTS_DATA['imagenes'])
    
    
    return RespuestaProcesamientoImgFacturas(factura=factura_ocr,clasificacion=clasificacion_groq,imagenes=data_img)

                    