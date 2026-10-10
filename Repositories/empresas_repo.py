import asyncio
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Integrations.r2_storage import r2_storage
from Models.Empresas import Empresas
from Models.MovimientosGastos import MovimientosGastos
from Schemas.Respuestas import RespuestaFuncion

from Utils.error_utils import limpiar_mensaje_error_bd

logger = logging.getLogger(__name__)


async def listar_empresas(db: AsyncSession):
    """Devuelve todas las empresas ordenadas por la más reciente."""
    try:
        cantidad_registros = (
            select(func.count(MovimientosGastos.Id))
            .where(MovimientosGastos.EmpresaId == Empresas.Id)
            .scalar_subquery()
        )
        result = await db.execute(
            select(Empresas, cantidad_registros.label("CantidadRegistros"))
            .order_by(Empresas.Id.desc())
        )

        empresas = [
            {
                **{
                    column.key: getattr(empresa, column.key)
                    for column in Empresas.__table__.columns
                },
                "CantidadRegistros": cantidad,
            }
            for empresa, cantidad in result.all()
        ]

        return RespuestaFuncion(data_registro=empresas)
    except Exception as error:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=str(error),
            )
async def listar_empresas_usuario(db: AsyncSession,id_usuario):
    """Devuelve todas las empresas ordenadas por uso y nombre."""
    try:
        cantidad_movimientos = (
            select(func.count(MovimientosGastos.Id))
            .where(
                MovimientosGastos.EmpresaId == Empresas.Id,
                MovimientosGastos.UsuarioId == id_usuario,
            )
            .scalar_subquery()
        )
        result = await db.execute(
            select(Empresas, cantidad_movimientos.label("cantidad_movimientos")).order_by(
                cantidad_movimientos.desc(),
                Empresas.NombreEmpresa.asc(),
            )
        )
        
        empresas = [
            {
                **{
                    column.key: getattr(empresa, column.key)
                    for column in Empresas.__table__.columns
                },
                "cantidad_movimientos": cantidad,
            }
            for empresa, cantidad in result.all()
        ]
        
        return RespuestaFuncion(data_registro=empresas)
    except Exception as error:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=str(error),
            )


async def registrar(db: AsyncSession, empresa: dict):
    """Registra o actualiza una empresa.

    empresa debe incluir:
    {id, nombre, ruc, logo_img}
    """
    try:
        if not empresa:
            return RespuestaFuncion(success_registro=False, mensaje="Datos de la empresa no proporcionados")

        empresa_id = empresa.get("id", 0) or 0
        nombre = str(empresa.get("nombre", "")).strip()
        rubro = empresa.get("rubro")
        if rubro is not None:
            rubro = str(rubro).strip()
        ruc = str(empresa.get("ruc", "")).strip()
        logo_img = empresa.get("logo_img")
        url_logo = None

        if logo_img is not None:
            try:
                file_bytes = await logo_img.read()
                file_name = getattr(logo_img, "filename", None) or "logo_empresa.jpg"
                if not file_bytes:
                    logger.warning("No se subió el logo de la empresa: el archivo está vacío")
                else:
                    resultado_subida = await asyncio.to_thread(
                        r2_storage.upload_logo_empresa,
                        file_bytes=file_bytes,
                        file_name=file_name,
                    )
                    if resultado_subida.get("success") and resultado_subida.get("url"):
                        url_logo = resultado_subida["url"]
                    else:
                        logger.warning(
                            "No se pudo subir el logo de la empresa: %s",
                            resultado_subida.get("message", "URL no disponible"),
                        )
            except Exception:
                logger.exception("Falló la carga del logo de la empresa")

        if not nombre:
            return RespuestaFuncion(success_registro=False, mensaje="El nombre de la empresa es obligatorio")

        if not ruc:
            return RespuestaFuncion(success_registro=False, mensaje="El RUC de la empresa es obligatorio")

        if empresa_id > 0:
            result = await db.execute(
                select(Empresas).where(Empresas.Id == empresa_id)
            )
            registro = result.scalars().first()
            if not registro:
                return RespuestaFuncion(success_registro=False, mensaje=f"Empresa con id {empresa_id} no encontrada")
            try:
                registro.NombreEmpresa = nombre
                registro.Ruc = ruc
                if rubro is not None:
                    registro.Rubro = rubro
                if logo_img is not None:
                    registro.UrlLogo = url_logo
                elif empresa.get("url_logo") is not None:
                    registro.UrlLogo = empresa["url_logo"]

                await db.commit()
                await db.refresh(registro)
            except Exception as e:
                await db.rollback()
                return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
            return RespuestaFuncion()

        
        empresa_existente = await db.execute(
            select(Empresas).where(Empresas.Ruc == ruc)
        )
        
        if empresa_existente.scalars().first():
            return RespuestaFuncion(success_registro=False, mensaje="Ya existe una empresa con ese RUC")
        try:
            nueva_empresa = Empresas(
                NombreEmpresa=nombre,
                Rubro=rubro,
                Ruc=ruc,
                UrlLogo=url_logo,
            )

            db.add(nueva_empresa)
            await db.commit()
            await db.refresh(nueva_empresa)
        except Exception as e:
            await db.rollback()
            return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
        return RespuestaFuncion()

    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False,  mensaje=limpiar_mensaje_error_bd(str(e)))


async def obtener_empresa(db: AsyncSession, empresa_id: int):
    result = await db.execute(
        select(Empresas).where(Empresas.Id == empresa_id)
    )
    return result.scalars().first()


async def eliminar_empresa(db: AsyncSession, empresa_id: int):
    if not empresa_id:
        return RespuestaFuncion(success_registro=False, mensaje="La empresa es obligatoria")

    empresa = await obtener_empresa(db, empresa_id)
    if not empresa:
        return RespuestaFuncion(success_registro=False, mensaje=f"Empresa con id {empresa_id} no encontrada")
    try:
        await db.delete(empresa)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    return RespuestaFuncion()

async def obtener_o_crear_empresa(db: AsyncSession, nombre:str, ruc:str,rubro:str):
    try:
        registro_empresa = await db.execute(
                        select(Empresas).where(Empresas.Ruc == ruc)
                    )
        empresa=registro_empresa.scalars().first()
        if not empresa:
            empresa_data = {
                    "id": 0,
                    "nombre": nombre,
                    "ruc": ruc,
                    "rubro":rubro,
                    "logo_img": "",
                }
            empresa=await registrar(db, empresa_data)
            if not empresa.success_registro:
                return RespuestaFuncion(success_registro=False, mensaje=empresa.mensaje)
            empresa = empresa.data_registro

        return RespuestaFuncion(data_registro=empresa)

    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))
    
