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
from Models.ErroresProcesamientoImagenesPendientes import TipoErrorEnum,ErroresProcesamientoImagenesPendientes
from Models.Usuarios import Usuarios
from Repositories.categorias_gastos_repo import obtener_o_crear_categoria
from Repositories.conceptos_gastos_repo import obtener_o_crear_conceptos
from Repositories.empresas_repo import obtener_o_crear_empresa
from Repositories.etiquetas_gastos_repo import obtener_o_crear_etiquetas
from Repositories.movimientos_gastos_repo import registrar
from Repositories.envio_correo_repo import registro_envio_correo
from Schemas.repos_schemas import RegistroErroresPendientes
from Services.img_factura_services import procesar_imagen_factura
from Services.email_service import RegistroPendienteData, enviar_correo_registro_pendiente
from DataTest.data import DATA_RESUMEN
from Utils.error_utils import limpiar_mensaje_error_bd
from Tasks.ejecutar_envio_correo import ejecutar_envios_pendientes

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
        tarea["imagenes"].append({
            "url": registro.UrlImagen,
            "size_bytes": registro.TamañoImagen,
            "success":True
        })
        tarea["ids"].append(registro.Id)

    return list(tareas.values())


async def marcar_estado(
    db,
    ids_pendientes: List[int],
    procesado: bool,
    mensaje_error: str = "",
    id_reg: Optional[int] = None,
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
        print(f"❌ Error en actualizacion de pendientes: {limpiar_mensaje_error_bd(str(exc))}")
        raise


async def registro_error(db,valores_reg: RegistroErroresPendientes, fecha_procesado: datetime):
    
    procesado = valores_reg.tipo_error != TipoErrorEnum.Modelo
    result = await db.execute(
        select(ImagenesPendientes.Id).where(
            ImagenesPendientes.CodigoTarea == valores_reg.tarea
        )
    )
    ids_pendientes = list(result.scalars().all())

    db.add(
        ErroresProcesamientoImagenesPendientes(
            CodigoTarea=valores_reg.tarea,
            TipoError=valores_reg.tipo_error,
            Error=valores_reg.error,
        )
    )
    await db.flush()

    await marcar_estado(
        db, ids_pendientes, procesado, valores_reg.error, None, fecha_procesado
    )


async def procesar_tarea(db, tarea: dict, fecha_procesado: datetime) -> int:
    """Procesa una tarea y retorna el id_reg del movimiento creado (0 si no se creó)."""
    codigo_tarea = tarea["codigo_tarea"]
    usuario_id = tarea["usuario_id"]
    urls = tarea["imagenes"]
    ids_pendientes = tarea["ids"]

    print(f"[TAREA {codigo_tarea}] INICIANDO PROCESAMIENTO]")

    paso_actual = ""

    try:
        paso_actual = "1. Descargar imágenes"
        print(f" --> {paso_actual}")
        imagenes_bytes: List[Tuple[bytes, str, str]] = []
        for imagen in urls:
            url = imagen["url"] if isinstance(imagen, dict) else imagen
            img = await descargar_imagen(url)
            size_bytes = imagen["size_bytes"] if isinstance(imagen, dict) else imagen
            imagenes_bytes.append((*img, url, str(size_bytes)))

        paso_actual = "2. Extraer y clasificar"
        print(f" --> {paso_actual}")
        resultado = await procesar_imagen_factura(
            imagenes=imagenes_bytes,
            upload_file=False,
            time_out_model=180,
            usuario_id=usuario_id,
            origen="Jobs",
            db=db,
        )

        if not resultado.procesamiento_correcto:
            tipo=TipoErrorEnum.Modelo if resultado.solicita_envio_pendiente else TipoErrorEnum.EstructuraDatos 
            error_export='Error en servicio de modelo' if resultado.solicita_envio_pendiente else resultado.mensaje_error
            error_data=RegistroErroresPendientes(
                tarea=codigo_tarea,
                tipo_error=tipo,
                error=resultado.mensaje_error
                )
            await registro_error(db,error_data,fecha_procesado)
            
            print(f"[TAREA {codigo_tarea}] Error extracción: {resultado.mensaje_error}")
            return 0,error_export

        factura = resultado.factura
        clasificacion = resultado.clasificacion

        

        paso_actual = "3. Registro completo"
        print(f" --> {paso_actual}")

        # ── CONCEPTOS ──
        registros_conceptos = await obtener_o_crear_conceptos(db, factura.detalle)
        if not registros_conceptos.success_registro:
            raise RuntimeError(f"Conceptos: {registros_conceptos.mensaje}")
        # data_registro = [1, 2, 3, ...] → {"CHIPA MESTIZO X K": 1, ...}
        mapa_conceptos = dict(zip(factura.detalle, registros_conceptos.data_registro))

        # ── EMPRESA ──
        registro_empresa = await obtener_o_crear_empresa(
            db,
            nombre=factura.empresa or "S/N",
            ruc=factura.ruc_empresa or "",
            rubro=factura.rubro or "",
        )
        if not registro_empresa.success_registro:
            raise RuntimeError(f"Empresa: {registro_empresa.mensaje}")

        # ── ETIQUETAS ──
        nombres_etiquetas = [e.etiqueta for e in clasificacion.etiquetas]
        registros_etiquetas = await obtener_o_crear_etiquetas(db, nombres_etiquetas)
        if not registros_etiquetas.success_registro:
            raise RuntimeError(f"Etiquetas: {registros_etiquetas.mensaje}")
        # data_registro = [92, 110] → {"Alimentacion": 92, "Envases": 110}
        mapa_etiquetas = dict(zip(nombres_etiquetas, registros_etiquetas.data_registro))

        # ── MAPEO CONCEPTO → ETIQUETA ──
        concepto_a_etiqueta: dict[str, int | None] = {}
        for etiqueta_obj in clasificacion.etiquetas:
            id_etiqueta = mapa_etiquetas.get(etiqueta_obj.etiqueta)
            for nombre_concepto in etiqueta_obj.conceptos:
                concepto_a_etiqueta[nombre_concepto] = id_etiqueta

        # ── LISTA FINAL DE CONCEPTOS CON SUS ETIQUETAS ──
        conceptos_con_etiquetas = [
            {
                "id_concepto": id_concepto,
                "id_etiqueta": concepto_a_etiqueta.get(nombre_concepto),
            }
            for nombre_concepto, id_concepto in mapa_conceptos.items()
        ]

        ids_etiquetas = list(mapa_etiquetas.values())

        # ── CATEGORÍA ──
        registro_categoria = await obtener_o_crear_categoria(
            db, clasificacion.categoria
        )
        if not registro_categoria.success_registro:
            raise RuntimeError(f"Categoria: {registro_categoria.mensaje}")
        id_categoria = registro_categoria.data_registro.Id

        try:
            fecha_gasto = (
                date.fromisoformat(factura.fecha)
                if factura.fecha
                else date.today()
            )
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
            "conceptos": conceptos_con_etiquetas,   # ← NUEVO FORMATO
            "etiquetas": ids_etiquetas,
            "model_img": factura.Model,
            "model_clasificador": clasificacion.modelo_clasificador,
            "id_stas":resultado.id_stats
        }

        registro_gasto = await registrar(db, movimiento_data)
        if not registro_gasto.success_registro:
            tipo=TipoErrorEnum.RegistroDato 
            error_data=RegistroErroresPendientes(
                tarea=codigo_tarea,
                tipo_error=tipo,
                error=registro_gasto.mensaje
                )
            await registro_error(db,error_data,fecha_procesado)
            
            print(f"[TAREA {codigo_tarea}] Error registro: {registro_gasto.mensaje}")
            return 0,registro_gasto.mensaje

        id_reg = registro_gasto.data_registro.Id
        print(" --> 4. Actualizacion de pendientes")
        await marcar_estado(db, ids_pendientes, True, "", id_reg, fecha_procesado)
        print(f"[TAREA {codigo_tarea}] Movimiento registrado: {id_reg}")
        return id_reg,''
        

    except Exception as exc:
        import traceback

        print(f"[TAREA {codigo_tarea}] ❌ Error en --> {paso_actual}: {exc}")
        traceback.print_exc()

        
        raise

async def main():
    # resumen = DATA_RESUMEN
    resumen = {}
    respuesta_correos=[]
    async with AsyncSessionLocal() as db:
        tareas = await obtener_tareas_pendientes(db)
        print(f"Tareas pendientes encontradas: {len(tareas)}")
        
        for tarea in tareas:
            fecha_procesado = datetime.now()
            usuario_id = str(tarea["usuario_id"])
            codigo_tarea = tarea["codigo_tarea"]
            id_reg = None

            try:
                id_reg,msg = await procesar_tarea(db, tarea, fecha_procesado)
                await db.commit()
            except Exception:
                await db.rollback()
                id_reg = 0
                msg=''
            finally:
                # if id_reg:
                registro = {
                    "codigo_tarea": codigo_tarea,
                    "id_reg": id_reg,
                    "fecha_hora_procesado": fecha_procesado.strftime("%d/%m/%y %H:%M:%S"),
                    "estado":  "🟢- Procesado" if id_reg>0 else "🔴- Error ",
                    "observacion": msg
                }
                resumen.setdefault(usuario_id, []).append(registro)
                await asyncio.sleep(60)
        if resumen:
            print("INICIO PROCESO DE COLA DE CORREO")
            for usuario_id, registros in resumen.items():
                usuario = await db.get(Usuarios, int(usuario_id))
                if not usuario or not usuario.Correo:
                    print(f"[CORREO] Usuario {usuario_id} sin correo registrado.")
                    continue

                correo = {
                    "destinatario": usuario.Correo,
                    "asunto": "Registro de imágenes pendientes procesadas",
                    "nombre_template": "registro_pendiente.html",
                    "data": [
                        {
                            "codigo_tarea": registro["codigo_tarea"],
                            "id_reg": registro["id_reg"],
                            "fecha_hora_procesado": registro["fecha_hora_procesado"],
                            "estado": registro["estado"],
                            "observacion": registro["observacion"],
                        }
                        for registro in registros
                    ],
                    "context_key": "registros",
                    "usuario_id": int(usuario_id),
                }

                respuesta = await registro_envio_correo(db, correo)
                if respuesta.success_registro:
                    print(f"[CORREO] Correo registrado para usuario {usuario_id}.")
                    respuesta_correos.append(respuesta.data_registro)
                else:
                    print(
                        f"[CORREO] No se pudo registrar correo para usuario {usuario_id}: {respuesta.mensaje}"
                    )
        else:
            print("NO HAY DATOS QUE NOTIFICAR")
    if respuesta_correos:
        for x in respuesta_correos:
            await ejecutar_envios_pendientes(x)
    # print("\n=== RESUMEN ===")
    # print(json.dumps(resumen, indent=2, ensure_ascii=False))
    
    print("\n=== FIN DEL PROCESO ===")
    return resumen


if __name__ == "__main__":
    asyncio.run(main())