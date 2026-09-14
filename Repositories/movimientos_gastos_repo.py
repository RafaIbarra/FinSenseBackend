from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession


from Models.CategoriasGastos import CategoriasGastos
from Models.Empresas import Empresas
from Models.MovimientosGastos import MovimientosGastos
from Models.MovimientosGastosImagenes import MovimientosGastosImagenes
from Models.MovimientosGastosConceptos import MovimientosGastosConceptos
from Models.MovimientosGastosEtiquetas import MovimientosGastosEtiquetas
from Models.EstadisticasModelos import EstadoEstadisticaEnum
from Repositories.urls_imagenes_temporales_repo import procesar_urls_temporales
from Repositories.datos_modelos_repo import actualizar_stast
from Integrations.r2_storage import *
from Schemas.Respuestas import RespuestaFuncion
from Schemas.repos_schemas import ActualizarEstadisticas
from Utils.error_utils import limpiar_mensaje_error_bd




async def obtener_movimiento(db: AsyncSession, movimiento_id: int, usuario_id: int):
    result = await db.execute(
        select(MovimientosGastos).where(
            MovimientosGastos.Id == movimiento_id,
            MovimientosGastos.UsuarioId == usuario_id,
        )
    )
    return result.scalars().first()


def _normalizar_imagenes(imagenes, type_url):
    """Deja 'imagenes' siempre como lista de dicts {url, size_bytes} y resuelve
    el valor real de 'type_url', sea que vengan sueltos o dentro de un dict
    {tipo_url, urls_img}."""
    if isinstance(imagenes, dict):
        type_url = imagenes.get("tipo_url", type_url)
        imagenes = imagenes.get("urls_img", [])

    imagenes = [
        imagen if isinstance(imagen, dict) else {"url": imagen, "size_bytes": 0}
        for imagen in imagenes
    ]
    type_url_valor = getattr(type_url, "value", type_url)
    return imagenes, type_url_valor


async def _procesar_imagenes_temporales(
    db: AsyncSession,
    usuario_id: int,
    imagenes: list,
    mover_a_permanente: bool,
):
    """Procesa (hasta 2) imagenes temporales.

    - mover_a_permanente=True: se usa al registrar un movimiento nuevo. Mueve
      cada imagen del bucket temporal al bucket definitivo de gastos y arma
      'urls_actualizar' con el detalle para la estadistica asociada.
    - mover_a_permanente=False: se usa cuando la factura ya existe (no se va a
      crear/actualizar el movimiento). Solo elimina las temporales, sin moverlas.

    Devuelve (imagenes_resultantes, urls_actualizar).
    """
    urls_procesadas = []
    urls_eliminadas = []
    urls_actualizar = []
    update_procesada=True
    for imagen_data in imagenes[:2]:
        img_url = imagen_data.get("url", "")

        if mover_a_permanente:
            resultado = r2_storage.move_between_buckets(
                source_url=img_url,
                source_bucket=r2_storage.bucket_temporales,
                dest_bucket=r2_storage.bucket_gastos,
            )
            if resultado.get("success"):
                url_permanente = resultado.get("url")
                urls_procesadas.append({
                    "url": url_permanente,
                    "size_bytes": imagen_data.get("size_bytes", 0),
                })
                urls_eliminadas.append(img_url)
                urls_actualizar.append({
                    "url_temporal": img_url,
                    "urls_permanente": url_permanente,
                })
        else:
            resultado = r2_storage.delete_temp_image(img_url)
            update_procesada=False
            if resultado.get("success"):
                urls_eliminadas.append(img_url)

    if urls_eliminadas:
        await procesar_urls_temporales(db, usuario_id, urls_eliminadas,update_procesada)

    imagenes_resultantes = urls_procesadas if mover_a_permanente else imagenes
    return imagenes_resultantes, urls_actualizar


async def _gestionar_imagenes(
    db: AsyncSession,
    usuario_id: int,
    imagenes,
    type_url,
    mover_a_permanente: bool,
):
    """Normaliza 'imagenes' y, si corresponde ('Temporal'), las procesa.

    Devuelve (imagenes_resultantes, urls_actualizar). Si no hay imagenes,
    devuelve ([], []) sin hacer nada mas.
    """
    if not imagenes:
        return [], []

    imagenes, type_url_valor = _normalizar_imagenes(imagenes, type_url)

    urls_actualizar = []
    if type_url_valor == "Temporal":
        imagenes, urls_actualizar = await _procesar_imagenes_temporales(
            db, usuario_id, imagenes, mover_a_permanente,
        )

    return imagenes, urls_actualizar


async def _actualizar_estadistica_si_corresponde(
    movimiento: dict,
    urls_actualizar: list,
    id_movimiento: int = None,
):
    """Si el movimiento trae 'id_stas' (> 0), marca la estadistica como
    Registrada y le adjunta las imagenes/movimiento resultantes.

    'id_movimiento' solo se envia a ActualizarEstadisticas cuando tiene un
    valor real: el schema lo espera como int obligatorio (no Optional), asi
    que pasarle None dispara un error de validacion de Pydantic.
    """
    estadistica_id = movimiento.get("id_stas", 0)
    
    if estadistica_id <= 0:
        return

    datos_stas = {
        "id": estadistica_id,
        "estado": (EstadoEstadisticaEnum.Registrada if id_movimiento is not None else EstadoEstadisticaEnum.Procesada),
        "imagenes": urls_actualizar,
    }
    if id_movimiento is not None:
        datos_stas["id_movimiento"] = id_movimiento

    upd_stas = ActualizarEstadisticas(**datos_stas)
    
    await actualizar_stast(upd_stas)


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
            return RespuestaFuncion(success_registro=False, mensaje=f"Categoría con id {categoria_id} no encontrada")

        nro_factura = movimiento.get("nro_factura")

        # Un mismo número de factura no puede repetirse para el mismo usuario y empresa,
        # excepto cuando la empresa tiene RUC "0-0" (empresa genérica/sin RUC).
        if empresa.Ruc != "0-0" and nro_factura:
            factura_query = select(MovimientosGastos).where(
                MovimientosGastos.UsuarioId == usuario_id,
                MovimientosGastos.EmpresaId == empresa.Id,
                MovimientosGastos.NumeroFactura == nro_factura,
                MovimientosGastos.IsActive==True
            )
            if movimiento_id > 0:
                factura_query = factura_query.where(MovimientosGastos.Id != movimiento_id)

            factura_result = await db.execute(factura_query)
            if factura_result.scalars().first():
                _, urls_actualizar = await _gestionar_imagenes(
                    db, usuario_id, imagenes, type_url, mover_a_permanente=False,
                )
                await _actualizar_estadistica_si_corresponde(movimiento, urls_actualizar)
                return RespuestaFuncion(
                    success_registro=False,
                    mensaje=f"Ya existe un movimiento registrado con la factura {nro_factura} para esta empresa",
                )

        if movimiento_id > 0:
            # Se valida que el movimiento pertenezca al usuario, para evitar
            # que un usuario actualice movimientos ajenos.
            result = await db.execute(
                select(MovimientosGastos).where(
                    MovimientosGastos.Id == movimiento_id,
                    MovimientosGastos.UsuarioId == usuario_id,
                )
            )
            registro = result.scalars().first()
            if not registro:
                
                return RespuestaFuncion(
                    success_registro=False,
                    mensaje=f"Movimiento con id {movimiento_id} no encontrado para el usuario",
                )

            try:
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

                # ── ETIQUETAS: se quitan las que ya no vienen y se agregan las nuevas ──
                # Se procesa en la MISMA transacción que la actualización del registro,
                # para que un fallo en cualquiera de los dos pasos revierta ambos.
                if "etiquetas" in movimiento:
                    etiquetas_nuevas = set(movimiento.get("etiquetas", []) or [])

                    etiquetas_actuales = await db.execute(
                        select(MovimientosGastosEtiquetas.EtiquetaId).where(
                            MovimientosGastosEtiquetas.MovimientoGastoId == movimiento_id
                        )
                    )
                    ids_actuales = {item[0] for item in etiquetas_actuales.all()}

                    ids_a_quitar = ids_actuales - etiquetas_nuevas
                    ids_a_agregar = etiquetas_nuevas - ids_actuales

                    if ids_a_quitar:
                        await db.execute(
                            delete(MovimientosGastosEtiquetas).where(
                                MovimientosGastosEtiquetas.MovimientoGastoId == movimiento_id,
                                MovimientosGastosEtiquetas.EtiquetaId.in_(ids_a_quitar),
                            )
                        )

                    if ids_a_agregar:
                        db.add_all([
                            MovimientosGastosEtiquetas(
                                MovimientoGastoId=movimiento_id,
                                EtiquetaId=etiqueta_id,
                            )
                            for etiqueta_id in sorted(ids_a_agregar)
                        ])

                await db.commit()
                await db.refresh(registro)
            except Exception as exc:
                await db.rollback()
                return RespuestaFuncion(
                    success_registro=False,
                    mensaje=f"No se pudo actualizar el movimiento: {limpiar_mensaje_error_bd(str(exc))}",
                )

            return RespuestaFuncion(data_registro=registro)
        else:
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
                ModeloExtraccionDatos=movimiento.get("model_img", ''),
                ModeloClasificador=movimiento.get("model_clasificador", '')
            )

            try:
                db.add(nuevo_movimiento)
                await db.flush()  # asigna nuevo_movimiento.Id sin comitear

                # ── CONCEPTOS CON ETIQUETA ──
                conceptos = movimiento.get("conceptos") or []
                if conceptos:
                    for concepto in conceptos:
                        if not concepto.get("id_concepto"):
                            raise ValueError("Cada concepto debe incluir 'id_concepto'")
                    db.add_all([
                        MovimientosGastosConceptos(
                            MovimientoGastoId=nuevo_movimiento.Id,
                            ConceptoId=concepto["id_concepto"],
                            EtiquetaId=concepto.get("id_etiqueta"),
                        )
                        for concepto in conceptos
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

            # Las imagenes se procesan y comitean en su propia transaccion
            imagenes, urls_actualizar = await _gestionar_imagenes(
                db, usuario_id, imagenes, type_url, mover_a_permanente=True,
            )
            if imagenes:
                for index, imagen_data in enumerate(imagenes[:2], start=1):
                    try:
                        imagen = MovimientosGastosImagenes(
                            UrlImagen=imagen_data.get("url", "") or "",
                            ReferenciaCola="",
                            MovimientoGastoId=nuevo_movimiento.Id,
                            ErrorUploadImg="",
                            TamañoImagen=imagen_data.get("size_bytes", 0),
                        )
                        db.add(imagen)
                    except Exception as exc:
                        print(f'Error procesando imagen {index}: {exc}')

                await db.commit()

            await _actualizar_estadistica_si_corresponde(
                movimiento, urls_actualizar, id_movimiento=nuevo_movimiento.Id,
            )
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

    imagenes_result = await db.execute(
        select(MovimientosGastosImagenes).where(MovimientosGastosImagenes.MovimientoGastoId == movimiento_id)
    )
    imagenes = imagenes_result.scalars().all()
    urls_imagenes = [img.UrlImagen for img in imagenes if img.UrlImagen]

    try:
        movimiento.IsActive = False

        for url_imagen in urls_imagenes:
            resultado = r2_storage.delete_gasto_image(url_imagen)
            if not resultado.get("success"):
                raise RuntimeError(
                    resultado.get("details")
                    or resultado.get("error")
                    or f"No se pudo eliminar la imagen en R2: {url_imagen}"
                )

        await db.commit()
        return RespuestaFuncion()
    except Exception as e:
        await db.rollback()
        return RespuestaFuncion(success_registro=False, mensaje=limpiar_mensaje_error_bd(str(e)))