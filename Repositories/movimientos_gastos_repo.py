from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.CategoriasGastos import CategoriasGastos
from Models.Empresas import Empresas
from Models.MovimientosGastos import MovimientosGastos
from Models.MovimientosGastosImagenes import MovimientosGastosImagenes
from Integrations.r2_storage import *
from Utils.img_works import registrar_imagenes
from Schemas.Respuestas import RespuestaFuncion
from Utils.error_utils import limpiar_mensaje_error_bd

async def obtener_movimiento(db: AsyncSession, movimiento_id: int, usuario_id: int):
    result = await db.execute(
        select(MovimientosGastos).where(
            MovimientosGastos.Id == movimiento_id,
            MovimientosGastos.UsuarioId == usuario_id,
        )
    )
    return result.scalars().first()


async def registrar(db: AsyncSession, movimiento: dict):
    """Registra o actualiza un movimiento de gasto.

    movimiento debe ser un diccionario con las claves:
    {id, user_id, total, iva_diez, iva_cinco, ruc, id_categoria, nro_factura, imagenes}
    """
    try:
        if not movimiento:
            return RespuestaFuncion(success_registro=False, mensaje="Datos del movimiento no proporcionados")

        ruc = movimiento.get("ruc")
        if not ruc:
            return RespuestaFuncion(success_registro=False, mensaje="El RUC de la empresa es obligatorio")

        empresa_result = await db.execute(select(Empresas).where(Empresas.Ruc == ruc))
        
        empresa = empresa_result.scalars().first()
        if not empresa:
            return RespuestaFuncion(success_registro=False, mensaje=f"Empresa con RUC {ruc} no encontrada")

        movimiento_id = movimiento.get("id", 0) or 0
        imagenes = movimiento.get("imagenes", [])
        categoria_id = movimiento.get("id_categoria")
        usuario_id = movimiento.get("user_id")

        if not categoria_id:
            return RespuestaFuncion(success_registro=False, mensaje="La categoría es obligatoria")

        categoria_result = await db.execute(
            select(CategoriasGastos).where(
                CategoriasGastos.Id == categoria_id,
                CategoriasGastos.UsuarioId == usuario_id,
            )
        )
        categoria = categoria_result.scalars().first()
        if not categoria:
            return RespuestaFuncion(success_registro=False, mensaje=f"Categoría con id {categoria_id} no encontrada para el usuario")

        nro_factura = movimiento.get("nro_factura")

        # Un mismo número de factura no puede repetirse para el mismo usuario y empresa,
        # excepto cuando la empresa tiene RUC "0-0" (empresa genérica/sin RUC).
        if empresa.Ruc != "0-0" and nro_factura:
            factura_query = select(MovimientosGastos).where(
                MovimientosGastos.UsuarioId == usuario_id,
                MovimientosGastos.EmpresaId == empresa.Id,
                MovimientosGastos.NumeroFactura == nro_factura,
            )
            if movimiento_id > 0:
                factura_query = factura_query.where(MovimientosGastos.Id != movimiento_id)

            factura_result = await db.execute(factura_query)
            if factura_result.scalars().first():
                return RespuestaFuncion(
                    success_registro=False,
                    mensaje=f"Ya existe un movimiento registrado con la factura {nro_factura} para esta empresa",
                )

        if movimiento_id > 0:
            result = await db.execute(select(MovimientosGastos).where(MovimientosGastos.Id == movimiento_id))
            registro = result.scalars().first()
            if not registro:
                return RespuestaFuncion(success_registro=False, mensaje=f"Movimiento con id {movimiento_id} no encontrado")

            if movimiento.get("user_id") is not None:
                registro.UsuarioId = movimiento["user_id"]
            if movimiento.get("total") is not None:
                registro.TotalGasto = movimiento["total"]
            if movimiento.get("iva_diez") is not None:
                registro.IvaDiez = movimiento["iva_diez"]
            if movimiento.get("iva_cinco") is not None:
                registro.IvaCinco = movimiento["iva_cinco"]
            if movimiento.get("id_categoria") is not None:
                registro.CategoriaId = movimiento["id_categoria"]
            if movimiento.get("nro_factura") is not None:
                registro.NumeroFactura = movimiento["nro_factura"]
            registro.EmpresaId = empresa.Id

            # Por ahora no hay lógica para imagenes cuando viene vacio
            await db.commit()
            await db.refresh(registro)
            return RespuestaFuncion()

        nuevo_movimiento = MovimientosGastos(
            UsuarioId=usuario_id,
            TotalGasto=movimiento.get("total", 0),
            IvaDiez=movimiento.get("iva_diez", 0),
            IvaCinco=movimiento.get("iva_cinco", 0),
            FechaGasto=movimiento.get("fecha_gasto"),
            TipoRegistro=movimiento.get("tipo_registro", "Manual"),
            CategoriaId=categoria_id,
            EmpresaId=empresa.Id,
            NumeroFactura=movimiento.get("nro_factura"),
        )

        db.add(nuevo_movimiento)
        await db.commit()
        await db.refresh(nuevo_movimiento)
        if imagenes:
            imagenes = imagenes if isinstance(imagenes, list) else [imagenes]
            for index, img in enumerate(imagenes[:2], start=1):
                try:
                    resultado = await registrar_imagenes(img, {"index": index})
                    url_imagen = resultado.get("url")
                    mensaje_imagen = resultado.get("mensaje", "")

                    imagen = MovimientosGastosImagenes(
                        UrlImagen=url_imagen or "",
                        ReferenciaCola="",
                        MovimientoGastoId=nuevo_movimiento.Id,
                        ErrorUploadImg=mensaje_imagen
                    )
                    db.add(imagen)

                except Exception as exc:
                    print(f'Error procesando imagen {index}: {exc}')

            await db.commit()

        return RespuestaFuncion()

    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))


async def eliminar_movimiento(db: AsyncSession, movimiento_id: int, usuario_id: int):
    if not movimiento_id:
        return RespuestaFuncion(success_registro=False, mensaje="El movimiento es obligatorio")

    movimiento = await obtener_movimiento(db, movimiento_id, usuario_id)
    if not movimiento:
        return RespuestaFuncion(success_registro=False, mensaje=f"Movimiento con id {movimiento_id} no encontrado para el usuario")

    try:
        await db.delete(movimiento)
        await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))