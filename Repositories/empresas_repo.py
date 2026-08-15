from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.Empresas import Empresas
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd

async def listar_empresas(db: AsyncSession):
    """Devuelve todas las empresas ordenadas por la más reciente."""
    result = await db.execute(
        select(Empresas).order_by(Empresas.Id.desc())
    )
    return result.scalars().all()


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
        ruc = str(empresa.get("ruc", "")).strip()
        logo_img = empresa.get("logo_img")
        url_logo = None

        if logo_img is not None:
            # Se recibe un archivo, se valida que exista y se prepara el flujo para
            # el almacenamiento real o la generación de URL pública en otra capa.
            # Aquí no se implementa el guardado ni la URL final.
            url_logo = getattr(logo_img, "filename", None) or None

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