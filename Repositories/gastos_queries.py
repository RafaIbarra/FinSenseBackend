from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from Models.MovimientosGastos import MovimientosGastos
from Models.MovimientosGastosConceptos import MovimientosGastosConceptos
from Models.MovimientosGastosEtiquetas import MovimientosGastosEtiquetas
from Models.ImagenesPendientes import ImagenesPendientes
from Models.Empresas import Empresas
from Models.CategoriasGastos import CategoriasGastos
from Schemas.file_format_schemas import ExcelIvaFormat
from Schemas.Respuestas import RespuestaFuncion

from Utils.error_utils import limpiar_mensaje_error_bd
from Utils.formateo_fechas import formatear_fecha_larga,formatear_fecha_corta

async def datos_iva_mes(db: AsyncSession, id_usuario: int, anno: int, mes: int):
    try:
        fecha_inicio = date(anno, mes, 1)
        fecha_fin = date(anno + (mes == 12), 1 if mes == 12 else mes + 1, 1)

        result = await db.execute(
            select(
                MovimientosGastos.FechaRegistro,
                MovimientosGastos.TotalGasto,
                MovimientosGastos.IvaDiez,
                MovimientosGastos.IvaCinco,
                MovimientosGastos.FechaGasto.label("FechaFactura"),
                MovimientosGastos.TipoRegistro,
                MovimientosGastos.NumeroFactura,
                Empresas.NombreEmpresa,
                Empresas.Ruc.label("NumeroRuc"),
                CategoriasGastos.NombreCategoria.label("Categoria"),
            )
            .outerjoin(MovimientosGastos.empresa)
            .outerjoin(MovimientosGastos.categoria)
            .where(
                MovimientosGastos.UsuarioId == id_usuario,
                MovimientosGastos.IsActive.is_(True),
                MovimientosGastos.FechaGasto >= fecha_inicio,
                MovimientosGastos.FechaGasto < fecha_fin,
            )
        )

        movimientos = result.mappings().all()
        data_excel=[ExcelIvaFormat.model_validate(movimiento)for movimiento in movimientos]
        return RespuestaFuncion(data_registro=data_excel)
    except Exception as exc:    
        return RespuestaFuncion(success_registro=False,mensaje=limpiar_mensaje_error_bd(str(exc)))
    

async def dashboard_usuario(db: AsyncSession, id_usuario: int, anno: int, mes: int):
    fecha_inicio = date(anno, mes, 1)
    fecha_fin = date(anno + (mes == 12), 1 if mes == 12 else mes + 1, 1)

    result = await db.execute(
        select(MovimientosGastos)
        .where(
            MovimientosGastos.UsuarioId == id_usuario,
            MovimientosGastos.IsActive.is_(True),
            MovimientosGastos.FechaGasto >= fecha_inicio,
            MovimientosGastos.FechaGasto < fecha_fin,
        )
        .options(
            selectinload(MovimientosGastos.empresa),
            selectinload(MovimientosGastos.categoria),
            selectinload(MovimientosGastos.etiquetas).selectinload(
                MovimientosGastosEtiquetas.etiqueta
            ),
        )
    )
    movimientos = result.scalars().all()

    pendientes_result = await db.execute(
        select(func.count(ImagenesPendientes.Id)).where(
            ImagenesPendientes.UsuarioId == id_usuario,
            ImagenesPendientes.Procesado.is_(False),
        )
    )

    def totales(registros):
        return {
            "total_gasto": sum(registro.TotalGasto or 0 for registro in registros),
            "iva_diez": sum(registro.IvaDiez or 0 for registro in registros),
            "iva_cinco": sum(registro.IvaCinco or 0 for registro in registros),
            "cantidad_registros": len(registros),
        }

    def acumular(agrupaciones, clave, nombre, registro):
        if clave not in agrupaciones:
            agrupaciones[clave] = {"id": clave, "nombre": nombre, "registros": []}
        agrupaciones[clave]["registros"].append(registro)

    por_empresa = {}
    por_categoria = {}
    por_etiqueta = {}
    primera_semana = fecha_inicio - timedelta(days=fecha_inicio.weekday())
    ultima_fecha_mes = fecha_fin - timedelta(days=1)
    ultima_semana = ultima_fecha_mes - timedelta(days=ultima_fecha_mes.weekday())
    por_semana = {}
    semana = primera_semana
    while semana <= ultima_semana:
        por_semana[semana] = {
            "desde_fecha": semana,
            "hasta_fecha": semana + timedelta(days=6),
            "registros": [],
        }
        semana += timedelta(days=7)

    for movimiento in movimientos:
        if movimiento.empresa:
            acumular(
                por_empresa,
                movimiento.empresa.Id,
                movimiento.empresa.NombreEmpresa,
                movimiento,
            )
        if movimiento.categoria:
            acumular(
                por_categoria,
                movimiento.categoria.Id,
                movimiento.categoria.NombreCategoria,
                movimiento,
            )
        for enlace in movimiento.etiquetas:
            if enlace.etiqueta:
                acumular(
                    por_etiqueta,
                    enlace.etiqueta.Id,
                    enlace.etiqueta.NombreEtiqueta,
                    movimiento,
                )

        semana_inicio = movimiento.FechaGasto - timedelta(
            days=movimiento.FechaGasto.weekday()
        )
        por_semana[semana_inicio]["registros"].append(movimiento)

    def serializar_agrupaciones(agrupaciones):
        return [
            {
                "id": clave,
                "nombre": datos["nombre"],
                **totales(datos["registros"]),
            }
            for clave, datos in sorted(agrupaciones.items(), key=lambda item: item[0])
        ]

    def serializar_semanas():
        return [
            {
                "desde_fecha": datos["desde_fecha"].strftime("%d/%m/%Y"),
                "hasta_fecha": datos["hasta_fecha"].strftime("%d/%m/%Y"),
                **totales(datos["registros"]),
            }
            for datos in por_semana.values()
        ]

    return {
        "totales": totales(movimientos),
        "por_empresa": serializar_agrupaciones(por_empresa),
        "por_categoria": serializar_agrupaciones(por_categoria),
        "por_etiqueta": serializar_agrupaciones(por_etiqueta),
        "por_semana": serializar_semanas(),
        "imagenes_pendientes_no_procesadas": pendientes_result.scalar_one(),
    }

async def movimientos_usuario_gastos(
    db: AsyncSession, id_usuario: int, mes: int = 0, anno: int = 0
):
    try: 
        if anno < 0 or mes < 0:
            return RespuestaFuncion(
                success_registro=False,
                mensaje="El año y el mes no pueden ser negativos.",
            )
        if mes > 0 and anno == 0:
            return RespuestaFuncion(
                success_registro=False,
                mensaje="Debe indicar un año cuando especifica un mes.",
            )
        if anno > 0 and mes != 0 and not 1 <= mes <= 12:
            return RespuestaFuncion(
                success_registro=False,
                mensaje="El mes debe estar entre 1 y 12.",
            )

        filtros = [
            MovimientosGastos.UsuarioId == id_usuario,
            MovimientosGastos.IsActive.is_(True),
        ]
        if anno > 0:
            fecha_inicio = date(anno, mes or 1, 1)
            fecha_fin = (
                date(anno + 1, 1, 1)
                if mes == 0
                else date(anno + (mes == 12), 1 if mes == 12 else mes + 1, 1)
            )
            
            filtros.extend(
                [
                    MovimientosGastos.FechaGasto >= fecha_inicio,
                    MovimientosGastos.FechaGasto < fecha_fin,
                ]
            )

        result = await db.execute(
            select(MovimientosGastos)
            .where(*filtros)
            .options(
                selectinload(MovimientosGastos.empresa),
                selectinload(MovimientosGastos.categoria),
                selectinload(MovimientosGastos.etiquetas).selectinload(
                    MovimientosGastosEtiquetas.etiqueta
                ),
                selectinload(MovimientosGastos.conceptos).selectinload(
                    MovimientosGastosConceptos.concepto
                ),
                selectinload(MovimientosGastos.conceptos).selectinload(
                    MovimientosGastosConceptos.etiqueta
                ),
                selectinload(MovimientosGastos.imagenes),
                selectinload(MovimientosGastos.imagenes_pendientes),
            )
            .order_by(MovimientosGastos.FechaRegistro.desc())
        )
        movimientos = result.scalars().all()

        

        def tareas_procesadas(movimiento):
            tipo_registro = movimiento.TipoRegistro.value if hasattr(movimiento.TipoRegistro, "value") else str(movimiento.TipoRegistro)
            if tipo_registro != "Automatico":
                return []

            tareas = {}
            for imagen in movimiento.imagenes_pendientes:
                if imagen.Procesado and imagen.CodigoTarea not in tareas:
                    tareas[imagen.CodigoTarea] = {
                        "codigo_tarea": imagen.CodigoTarea,
                        "fecha_procesado": imagen.FechaProcesado.strftime("%d/%m/%Y %H:%M:%S") if imagen.FechaProcesado else None,
                    }
            return list(tareas.values())

        data= [
            {
                "id": movimiento.Id,
                "fecha_registro": formatear_fecha_larga(movimiento.FechaRegistro),
                "fecha_gasto": formatear_fecha_corta(movimiento.FechaGasto),
                "total_gasto": movimiento.TotalGasto,
                "iva_diez": movimiento.IvaDiez,
                "iva_cinco": movimiento.IvaCinco,
                "tipo_registro": movimiento.TipoRegistro.value if hasattr(movimiento.TipoRegistro, "value") else str(movimiento.TipoRegistro),
                "categoria_id": movimiento.CategoriaId,
                "empresa_id": movimiento.EmpresaId,
                "empresa": {
                    "id": movimiento.empresa.Id,
                    "nombre": movimiento.empresa.NombreEmpresa,
                    "ruc": movimiento.empresa.Ruc,
                    "url_logo": movimiento.empresa.UrlLogo,
                } if movimiento.empresa else None,
                "categoria": {
                    "id": movimiento.categoria.Id,
                    "nombre": movimiento.categoria.NombreCategoria,
                } if movimiento.categoria else None,
                "numero_factura": movimiento.NumeroFactura,
                "modelo_extraccion_datos": movimiento.ModeloExtraccionDatos,
                "modelo_clasificador": movimiento.ModeloClasificador,
                "tareas_procesadas": tareas_procesadas(movimiento),
                "etiquetas": [
                    {
                        "idetiqueta": enlace.EtiquetaId,
                        "nombre": enlace.etiqueta.NombreEtiqueta,
                    }
                    for enlace in movimiento.etiquetas
                ],
                "conceptos": [
                    {
                        "idconcepto": enlace.ConceptoId,
                        "nombre": enlace.concepto.NombreConcepto,
                        "etiqueta": {
                            "id": enlace.EtiquetaId,
                            "nombre": enlace.etiqueta.NombreEtiqueta,
                        } if enlace.etiqueta else None,
                    }
                    for enlace in movimiento.conceptos
                ],
                "imagenes": [imagen.UrlImagen for imagen in movimiento.imagenes],
            }
            for movimiento in movimientos
        ]
        return RespuestaFuncion(data_registro=data)
    except Exception as exc:    
        return RespuestaFuncion(success_registro=False,mensaje=limpiar_mensaje_error_bd(str(exc)))

    
async def listar_imagenes_pendientes_usuario(db: AsyncSession, id_usuario: int):
    result = await db.execute(
        select(ImagenesPendientes)
        .where(ImagenesPendientes.UsuarioId == id_usuario)
        .options(
            with_loader_criteria(
                MovimientosGastos,
                MovimientosGastos.IsActive.is_(True),
            ),
            selectinload(ImagenesPendientes.movimiento).selectinload(
                MovimientosGastos.categoria
            ),
            selectinload(ImagenesPendientes.movimiento).selectinload(
                MovimientosGastos.empresa
            ),
            selectinload(ImagenesPendientes.movimiento)
            .selectinload(MovimientosGastos.etiquetas)
            .selectinload(MovimientosGastosEtiquetas.etiqueta),
        )
        .order_by(ImagenesPendientes.FechaRegistro.desc())
    )
    imagenes = result.scalars().all()

    

    return [
        {
            "id": imagen.Id,
            "codigo_tarea": imagen.CodigoTarea,
            "url_imagen": imagen.UrlImagen,
            "fecha_registro": formatear_fecha_larga(imagen.FechaRegistro),
            "motivo": imagen.Motivo,
            "procesado": imagen.Procesado,
            "fecha_procesado": formatear_fecha_larga(imagen.FechaProcesado),
            "movimiento": {
                "id": movimiento.Id,
                "categoria": {
                    "id": movimiento.categoria.Id,
                    "nombre": movimiento.categoria.NombreCategoria,
                } if movimiento.categoria else None,
                "etiquetas": [
                    {
                        "id": enlace.EtiquetaId,
                        "nombre": enlace.etiqueta.NombreEtiqueta,
                    }
                    for enlace in movimiento.etiquetas
                ],
                "numero_factura": movimiento.NumeroFactura,
                "empresa": {
                    "id": movimiento.empresa.Id,
                    "nombre": movimiento.empresa.NombreEmpresa,
                    "ruc": movimiento.empresa.Ruc,
                    "url_logo": movimiento.empresa.UrlLogo,
                } if movimiento.empresa else None,
                "total_gasto": movimiento.TotalGasto,
            } if (movimiento := imagen.movimiento) else None,
        }
        for imagen in imagenes
    ]