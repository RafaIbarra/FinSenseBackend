from typing import  Optional,List,Tuple

from Integrations.google_ocr_client import extraer_factura
from Integrations.groq_clasificador import clasificar_gasto
from Schemas.Respuestas import RespuestaProcesamientoImgFacturas
from Schemas.r2_storage_schemas import RespuestaImagenesSubidas
from Schemas.integrations_schemas import FacturaExtraida,ClasificacionGasto
from Utils.img_works import registrar_lista_imagenes
from DataTest.data import TESTS_DATA

async def procesar_imagen_factura(imagenes: List[Tuple[bytes, str, str]],upload_file:bool=True):
    
    factura_ocr: Optional[FacturaExtraida] = None
    clasificacion_groq: Optional[ClasificacionGasto] = None
    data_img:Optional[RespuestaImagenesSubidas] = None
    data_respuesta:Optional[RespuestaProcesamientoImgFacturas] = None

    imagen_1, mime_type_1, filename_1 = imagenes[0]
    imagen_2, mime_type_2, filename_2 = None, "image/jpeg", "factura.jpg"

    if len(imagenes) > 1:
        imagen_2, mime_type_2, filename_2 = imagenes[1]
    
    factura_ocr = await extraer_factura(
                imagen_1=imagen_1,
                imagen_2=imagen_2,
                mime_type_1=mime_type_1,
                mime_type_2=mime_type_2,
                time_out=180,
            )
    # factura_ocr=FacturaExtraida(**TESTS_DATA['factura'])
    
    if not factura_ocr.success_registro:
        return RespuestaProcesamientoImgFacturas(procesamiento_correcto=False,solicita_envio_pendiente=True,mensaje_error=factura_ocr.mensaje_error)
    
    if not factura_ocr.data_correct:
        return RespuestaProcesamientoImgFacturas(procesamiento_correcto=False,solicita_envio_pendiente=False,mensaje_error=factura_ocr.mensaje_error)

    clasificacion_groq = await clasificar_gasto(
                {
                    "empresa": factura_ocr.empresa,
                    "rubro_empresa": factura_ocr.rubro,
                    "conceptos": factura_ocr.detalle,
                },
                time_out=180,
            )
    # clasificacion_groq=ClasificacionGasto(**TESTS_DATA['clasificacion'])
    if upload_file:
        imagenes_para_subir = [(imagen_1, filename_1),]
        if imagen_2:
            imagenes_para_subir.append((imagen_2, filename_2))

        data_img=await registrar_lista_imagenes(imagenes_para_subir)
    else:
        data_img=None
    # data_img=RespuestaImagenesSubidas(**TESTS_DATA['imagenes'])
    
    
    return RespuestaProcesamientoImgFacturas(factura=factura_ocr,clasificacion=clasificacion_groq,imagenes=data_img)
                    