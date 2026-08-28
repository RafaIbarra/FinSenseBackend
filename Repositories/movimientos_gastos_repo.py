from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from Models.CategoriasGastos import CategoriasGastos
from Models.Empresas import Empresas
from Models.MovimientosGastos import MovimientosGastos
from Models.MovimientosGastosImagenes import MovimientosGastosImagenes
from Models.MovimientosGastosConceptos import MovimientosGastosConceptos
from Models.MovimientosGastosEtiquetas import MovimientosGastosEtiquetas
from Repositories.urls_imagenes_temporales_repo import procesar_urls_temporales
from Integrations.r2_storage import *
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
        type_url = movimiento.get("type_url", "")
        categoria_id = movimiento.get("id_categoria")
        usuario_id = movimiento.get("user_id")

        if not categoria_id:
            return RespuestaFuncion(success_registro=False, mensaje="La categoría es obligatoria")

        categoria_result = await db.execute(
            select(CategoriasGastos).where(
                CategoriasGastos.Id == categoria_id,
                
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
            if movimiento.get("model_img") is not None:
                registro.ModeloExtraccionDatos = movimiento["model_img"]
            if movimiento.get("model_clasificador") is not None:
                registro.ModeloClasificador = movimiento["model_clasificador"]
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
            ModeloExtraccionDatos= movimiento.get("model_img",'') ,
            ModeloClasificador= movimiento.get("model_clasificador",'') 
        )

        
        try:
            db.add(nuevo_movimiento)
            await db.flush()  # asigna nuevo_movimiento.Id sin comitear

            if movimiento.get("conceptos", []):
                db.add_all([
                    MovimientosGastosConceptos(
                        MovimientoGastoId=nuevo_movimiento.Id,
                        ConceptoId=concepto_id,
                    )
                    for concepto_id in movimiento["conceptos"]
                ])
            if movimiento.get("etiquetas", []):
                db.add_all([
                    MovimientosGastosEtiquetas(
                        MovimientoGastoId=nuevo_movimiento.Id,
                        EtiquetaId=etiqueta_id,
                    )
                    for etiqueta_id in movimiento["etiquetas"]
                ])

            await db.commit()
            await db.refresh(nuevo_movimiento)
        except Exception as exc:
            await db.rollback()
            return RespuestaFuncion(
                success_registro=False,
                mensaje=f"No se pudo registrar el movimiento: {limpiar_mensaje_error_bd(str(exc))}",
            )

        # Las imagenes se procesan y comitean en su propia transaccion, DESPUÉS de que
        # movimiento+conceptos+etiquetas ya quedaron confirmados. Un error acá NO debe
        # afectar a lo anterior, y de hecho cada imagen ya maneja su propio try/except
        # individual (si falla la subida a R2, se guarda con ErrorUploadImg y se sigue
        # con la siguiente, sin abortar nada).
        if imagenes:
            imagenes = imagenes if isinstance(imagenes, list) else [imagenes]
            type_url_valor = getattr(type_url, 'value', type_url)
            # Si vienen del bucket de escaneadas, las copiamos a gastos antes de registrar
            
            if type_url_valor  == "Temporal":
                
                urls_procesadas = []
                urls_eliminadas = []
                for img_url in imagenes[:2]:
                    resultado = r2_storage.move_between_buckets(
                        source_url=img_url,
                        source_bucket=r2_storage.bucket_temporales,
                        dest_bucket=r2_storage.bucket_gastos,
                    )
                    if resultado.get("success"):
                        urls_procesadas.append(resultado.get("url"))
                        urls_eliminadas.append(img_url)
                if urls_eliminadas:
                   await procesar_urls_temporales(db,usuario_id,urls_eliminadas)
                imagenes = urls_procesadas

            for index, img in enumerate(imagenes[:2], start=1):
                try:
                    imagen = MovimientosGastosImagenes(
                        UrlImagen=img or "",
                        ReferenciaCola="",
                        MovimientoGastoId=nuevo_movimiento.Id,
                        ErrorUploadImg=""
                    )
                    db.add(imagen)

                except Exception as exc:
                    print(f'Error procesando imagen {index}: {exc}')

            await db.commit()

        return RespuestaFuncion(data_registro=nuevo_movimiento)

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