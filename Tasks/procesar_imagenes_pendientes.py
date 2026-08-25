import asyncio
import sys
from datetime import date
from pathlib import Path
from typing import List, Tuple,Optional
from urllib.parse import urlparse
from datetime import datetime
import json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload

from Config.settings import AsyncSessionLocal
from Models.ImagenesPendientes import ImagenesPendientes
from Models.MovimientosGastos import TipoRegistroEnum
from Models.Usuarios import Usuarios
from Repositories.categorias_gastos_repo import obtener_o_crear_categoria
from Repositories.conceptos_gastos_repo import obtener_o_crear_conceptos
from Repositories.empresas_repo import obtener_o_crear_empresa
from Repositories.etiquetas_gastos_repo import obtener_o_crear_etiquetas
from Repositories.movimientos_gastos_repo import registrar
from Services.img_factura_services import procesar_imagen_factura
from Services.email_service import RegistroPendienteData, enviar_correo_registro_pendiente
from DataTest.data import DATA_RESUMEN
from Utils.error_utils import limpiar_mensaje_error_bd
async def descargar_imagen(url: str) -> Tuple[bytes, str, str]:
    """Descarga una imagen desde URL y devuelve (bytes, content_type, filename)."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()

        content = response.content
        content_type = response.headers.get("content-type", "image/jpeg")
        filename = Path(urlparse(url).path).name or "factura.jpg"

        return content, content_type, filename


async def obtener_tareas_pendientes(db):
    """Agrupa las imágenes pendientes por código de tarea (máximo 5 tareas)."""
    primeras_tareas = (
        select(
            ImagenesPendientes.CodigoTarea,
            func.min(ImagenesPendientes.FechaRegistro).label("fecha_tarea"),
        )
        .where(ImagenesPendientes.Procesado.is_(False))
        .group_by(ImagenesPendientes.CodigoTarea)
        .order_by(func.max(ImagenesPendientes.FechaRegistro).asc())
        .limit(5)
        .subquery()
    )

    result = await db.execute(
        select(ImagenesPendientes)
        .join(
            primeras_tareas,
            ImagenesPendientes.CodigoTarea == primeras_tareas.c.CodigoTarea,
        )
        .where(ImagenesPendientes.Procesado.is_(False))
        .options(selectinload(ImagenesPendientes.usuario))
        .order_by(
            primeras_tareas.c.fecha_tarea.asc(),
            ImagenesPendientes.FechaRegistro.asc(),
            ImagenesPendientes.Id.asc(),
        )
    )
    registros = result.scalars().all()

    tareas = {}
    for registro in registros:
        tarea = tareas.setdefault(
            registro.CodigoTarea,
            {
                "codigo_tarea": registro.CodigoTarea,
                "usuario_id": registro.UsuarioId,
                "fecha_registro": registro.FechaRegistro,
                "imagenes": [],
                "ids": [],
            },
        )
        tarea["imagenes"].append(registro.UrlImagen)
        tarea["ids"].append(registro.Id)

    return list(tareas.values())


async def marcar_estado(
    db,
    ids_pendientes: List[int],
    procesado: bool,
    mensaje_error: str = "",
    id_reg: int = 0,
    fecha_procesado: datetime = None,
):
    if fecha_procesado is None:
        fecha_procesado = func.now()
    try:
        await db.execute(
            update(ImagenesPendientes)
            .where(ImagenesPendientes.Id.in_(ids_pendientes))
            .values(
                Procesado=procesado,
                FechaProcesado=fecha_procesado,
                MovimientoId=id_reg,
            )
        )
    except Exception as exc:
        print(f"❌ Error en actualizacion de pendientes: {limpiar_mensaje_error_bd(exc)}")
        raise


async def notificar_resumen(db, resumen: dict):
    if not resumen:
        return

    ids_usuarios = [int(usuario_id) for usuario_id in resumen]
    result = await db.execute(
        select(Usuarios).where(Usuarios.Id.in_(ids_usuarios))
    )
    usuarios = {str(usuario.Id): usuario for usuario in result.scalars().all()}

    for usuario_id, registros in resumen.items():
        usuario = usuarios.get(str(usuario_id))
        if not usuario or not usuario.Correo:
            print(f"[NOTIFICACION] Usuario {usuario_id} sin correo registrado.")
            continue

        datos_registros = [
            RegistroPendienteData(
                codigo_tarea=registro["codigo_tarea"],
                id_reg=registro["id_reg"],
                fecha_hora_procesado=registro["fecha_hora_procesado"],
            )
            for registro in registros
        ]
        await enviar_correo_registro_pendiente(
            usuario.Correo,
            "Registro de imágenes pendientes procesadas",
            datos_registros,
        )
        print(f"[NOTIFICACION] Correo enviado al usuario {usuario_id}.")

async def procesar_tarea(db, tarea: dict, fecha_procesado: datetime) -> int:
    """Procesa una tarea y retorna el id_reg del movimiento creado (0 si no se creó)."""
    codigo_tarea = tarea["codigo_tarea"]
    usuario_id = tarea["usuario_id"]
    urls = tarea["imagenes"]
    ids_pendientes = tarea["ids"]

    print(f"[TAREA {codigo_tarea}] INICIANDO PROCESAMIENTO]")

    try:
        print(" --> 1. Descargar imágenes")
        imagenes_bytes: List[Tuple[bytes, str, str]] = []
        for url in urls:
            img = await descargar_imagen(url)
            imagenes_bytes.append(img)

        print(" --> 2. Extraer y clasificar")
        
        resultado = await procesar_imagen_factura(imagenes_bytes, upload_file=False)

        if not resultado.procesamiento_correcto:
            await marcar_estado(
                db, ids_pendientes, True, resultado.mensaje_error, 0, fecha_procesado
            )
            print(f"[TAREA {codigo_tarea}] Error extracción: {resultado.mensaje_error}")
            return 0

        factura = resultado.factura
        clasificacion = resultado.clasificacion

        if not factura.data_correct:
            await marcar_estado(
                db, ids_pendientes, True, factura.mensaje_error, 0, fecha_procesado
            )
            print(f"[TAREA {codigo_tarea}] Datos incorrectos: {factura.mensaje_error}")
            return 0

        print(" --> 3. Registro completo")
        ids_conceptos = []
        if factura.detalle:
            registros_conceptos = await obtener_o_crear_conceptos(db, factura.detalle)
            if not registros_conceptos.success_registro:
                raise RuntimeError(f"Conceptos: {registros_conceptos.mensaje}")
            ids_conceptos = registros_conceptos.data_registro

        registro_empresa = await obtener_o_crear_empresa(
            db,
            nombre=factura.empresa or "S/N",
            ruc=factura.ruc_empresa or "",
            rubro=factura.rubro or "",
        )
        if not registro_empresa.success_registro:
            print(f" ❌ Error registro empresa {registro_empresa.mensaje}")
            raise RuntimeError(f"Empresa: {registro_empresa.mensaje}")

        ids_etiquetas = []
        if clasificacion.etiquetas:
            registros_etiquetas = await obtener_o_crear_etiquetas(db, clasificacion.etiquetas)
            if not registros_etiquetas.success_registro:
                print(f" ❌ Error registro Etiquetas {registros_etiquetas.mensaje}")
                raise RuntimeError(f"Etiquetas: {registros_etiquetas.mensaje}")
            ids_etiquetas = registros_etiquetas.data_registro

        registro_categoria = await obtener_o_crear_categoria(db, clasificacion.categoria)
        if not registro_categoria.success_registro:
            print(f" ❌ Error registro Categoria {registro_categoria.mensaje}")
            raise RuntimeError(f"Categoria: {registro_categoria.mensaje}")
        id_categoria = registro_categoria.data_registro.Id

        try:
            fecha_gasto = date.fromisoformat(factura.fecha) if factura.fecha else date.today()
        except ValueError:
            fecha_gasto = date.today()

        movimiento_data = {
            "id": 0,
            "user_id": usuario_id,
            "total": int(factura.total or 0),
            "iva_diez": int(factura.iva_diez or 0),
            "iva_cinco": int(factura.iva_cinco or 0),
            "ruc": factura.ruc_empresa or "",
            "id_categoria": id_categoria,
            "nro_factura": factura.numero_factura,
            "imagenes": urls,
            "tipo_registro": TipoRegistroEnum.Automatico,
            "fecha_gasto": fecha_gasto,
            "conceptos": ids_conceptos,
            "etiquetas": ids_etiquetas,
            "model_img": factura.Model,
            "model_clasificador": clasificacion.modelo_clasificador,
        }

        registro_gasto = await registrar(db, movimiento_data)
        if not registro_gasto.success_registro:
            print(f" ❌ Error registro movimiento {registro_gasto.mensaje}")
            raise RuntimeError(f"Movimiento: {registro_gasto.mensaje}")

        id_reg = registro_gasto.data_registro.Id
        print(" --> 4. Actualizacion de pendientes")
        await marcar_estado(db, ids_pendientes, True, "", id_reg, fecha_procesado)
        print(f"[TAREA {codigo_tarea}] Movimiento registrado: {id_reg}")
        return id_reg

    except Exception as exc:
        await marcar_estado(db, ids_pendientes, True, str(exc), 0, fecha_procesado)
        print(f"[TAREA {codigo_tarea}] Error: {exc}")
        raise


async def main():
    # resumen = DATA_RESUMEN
    resumen = {}

    async with AsyncSessionLocal() as db:
        tareas = await obtener_tareas_pendientes(db)
        print(f"Tareas pendientes encontradas: {len(tareas)}")

        for tarea in tareas:
            fecha_procesado = datetime.now()
            usuario_id = str(tarea["usuario_id"])
            codigo_tarea = tarea["codigo_tarea"]
            id_reg = None

            try:
                id_reg = await procesar_tarea(db, tarea, fecha_procesado)
                await db.commit()
            except Exception:
                await db.rollback()
                id_reg = 0
            finally:
                if id_reg:
                    registro = {
                        "codigo_tarea": codigo_tarea,
                        "id_reg": id_reg,
                        "fecha_hora_procesado": fecha_procesado.strftime("%d/%m/%y %H:%M:%S"),
                    }
                    resumen.setdefault(usuario_id, []).append(registro)
                await asyncio.sleep(60)
        if resumen:
            print("INICIO PROCESO DE NOTIFICACION")
            await notificar_resumen(db, resumen)
        else:
            print("NO HAY DATOS QUE NOTIFICAR")
    
    # print("\n=== RESUMEN ===")
    # print(json.dumps(resumen, indent=2, ensure_ascii=False))
    
    print("\n=== FIN DEL PROCESO ===")
    return resumen


if __name__ == "__main__":
    asyncio.run(main())