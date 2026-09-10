from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .generacion_archivos_excel import generar_excel_mes
from Repositories.gastos_queries import datos_iva_mes
from Models.Usuarios import Usuarios
from Schemas.Respuestas import RespuestaFuncion
from Services.email_service import enviar_correo_con_adjunto
async def generar_y_enviar_excel_iva(db: AsyncSession,mes: int,anno:int ,id_usuario: int):
    try:
        datos_consulta=await datos_iva_mes(db,id_usuario,anno,mes)
        if not datos_consulta.success_registro:
            return RespuestaFuncion(success_registro=False,mensaje=datos_consulta.mensaje)
            
        valores=datos_consulta.data_registro

        result_excel=await generar_excel_mes(db,mes,anno,valores)

        if not result_excel.success_registro:
            return RespuestaFuncion(success_registro=False,mensaje=result_excel.mensaje)

        excel=result_excel.data_registro

        resultado_usuario = await db.execute(select(Usuarios).where(Usuarios.Id == id_usuario))

        usuario = resultado_usuario.scalars().first()
        if usuario is None:
            return RespuestaFuncion(success_registro=False,mensaje="No se encontró el usuario",)
        
        e_mail=usuario.Correo
        file_name=f"IVA {mes:02d}-{anno}.xlsx"
        
        resultado_enviar=await enviar_correo_con_adjunto(destinatario=e_mail,asunto="EXCEL IVA",adjunto=excel,nombre_adjunto=file_name)
        
        if not resultado_enviar.success_registro:
            return RespuestaFuncion(success_registro=False,mensaje=resultado_enviar.mensaje)
        
        return RespuestaFuncion(mensaje=f"El archivo será enviado a su correo {e_mail}")
        
    except Exception as e:
        return RespuestaFuncion(success_registro=False,mensaje=f"Error en el proceso de generación/envío del Excel de IVA: {str(e)}")
        
