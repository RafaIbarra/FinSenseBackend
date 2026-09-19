from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator
from Utils.formateo_fechas import formatear_fecha_corta, formatear_fecha_larga


class TokensResumenResponse(BaseModel):
    InputTokens: int
    OutputTokens: int
    ThoughtsTokens: int
    TotalTokens: int


class EstadisticasModelosResumenResponse(BaseModel):
    Cantidad: int
    Tokens: TokensResumenResponse


class ImagenesPendientesResumenResponse(BaseModel):
    Cantidad: int
    TareasNoProcesadas: int
    TotalTamañoImagenNoProcesadas: int

class ImagenesReportadasResumenResponse(BaseModel):
    Cantidad: int
    Pendiente: int
    Resuelto: int


class TamañoImagenesMovimientosResponse(BaseModel):
    Activos: int
    NoActivos: int
    Total: int


class MovimientosGastosResumenResponse(BaseModel):
    Cantidad: int
    Activos: int
    NoActivos: int
    TamañoImagen: TamañoImagenesMovimientosResponse


class ConexionPorFechaResponse(BaseModel):
    Fecha: str
    Cantidad: int


class SesionActivaResponse(BaseModel):
    Dispositivo: str
    Ip: str
    FechaConexion: str
    Movil: str


class SesionesResumenResponse(BaseModel):
    Cantidad: int
    Dispositivos: list[str]
    Ips: list[str]
    FechasConexion: list[ConexionPorFechaResponse]
    SesionesActivas: list[SesionActivaResponse]


class UsuarioResumenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Id: int
    NombreUsuario: str
    ApellidoUsuario: str
    UserName: str
    Correo: str
    FechaRegistro: datetime
    IsAdmin: bool

    EstadisticasModelos: EstadisticasModelosResumenResponse
    ImagenesPendientes: ImagenesPendientesResumenResponse
    ImagenesReportadas: ImagenesReportadasResumenResponse
    MovimientosGastos: MovimientosGastosResumenResponse
    Sesiones: SesionesResumenResponse

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return formatear_fecha_larga(value)

    @model_validator(mode="before")
    @classmethod
    def _calculo(cls, obj):
        # --- estadisticas_modelos: totales de tokens ---
        estadisticas = getattr(obj, "estadisticas_modelos", None) or []
        input_t = output_t = thoughts_t = total_t = 0
        for e in estadisticas:
            for d in getattr(e, "detalles", None) or []:
                input_t += d.InputTokens or 0
                output_t += d.OutputTokens or 0
                thoughts_t += d.ThoughtsTokens or 0
                total_t += d.TotalTokens or 0

        obj.EstadisticasModelos = {
            "Cantidad": len(estadisticas),
            "Tokens": {
                "InputTokens": input_t,
                "OutputTokens": output_t,
                "ThoughtsTokens": thoughts_t,
                "TotalTokens": total_t,
            },
        }

        # --- imagenes_pendientes ---
        img_pend = getattr(obj, "imagenes_pendientes", None) or []

        codigos_distintos = {img.CodigoTarea for img in img_pend}
        codigos_no_procesados = {img.CodigoTarea for img in img_pend if not img.Procesado}
        total_tam_no_procesadas = sum(
            img.TamañoImagen or 0 for img in img_pend if not img.Procesado
        )

        obj.ImagenesPendientes = {
            "Cantidad": len(codigos_distintos),
            "TareasNoProcesadas": len(codigos_no_procesados),
            "TotalTamañoImagenNoProcesadas": total_tam_no_procesadas,
        }
        # --- imagenes_reportadas ---
        img_rep = getattr(obj, "imagenes_reportadas", None) or []
        pendientes = sum(1 for img in img_rep if img.EstadoResolucion and img.EstadoResolucion.value == "Pendiente")
        resueltos = sum(1 for img in img_rep if img.EstadoResolucion and img.EstadoResolucion.value == "Resuelto")

        obj.ImagenesReportadas = {
            "Cantidad": len(img_rep),
            "Pendiente": pendientes,
            "Resuelto": resueltos,
        }

        # --- movimientos_gastos ---
        movs = getattr(obj, "movimientos_gastos", None) or []
        activos = sum(1 for m in movs if m.IsActive)
        no_activos = len(movs) - activos

        tam_activos = 0
        tam_no_activos = 0
        for m in movs:
            tam = sum(img.TamañoImagen or 0 for img in getattr(m, "imagenes", None) or [])
            if m.IsActive:
                tam_activos += tam
            else:
                tam_no_activos += tam

        obj.MovimientosGastos = {
            "Cantidad": len(movs),
            "Activos": activos,
            "NoActivos": no_activos,
            "TamañoImagen": {
                "Activos": tam_activos,
                "NoActivos": tam_no_activos,
                "Total": tam_activos + tam_no_activos,
            },
        }

        # --- sesiones ---
        sesiones = getattr(obj, "sesiones_activas", None) or []
        conexiones_por_fecha = {}
        for sesion in sesiones:
            fecha = formatear_fecha_corta(sesion.FechaConexion)
            conexiones_por_fecha[fecha] = conexiones_por_fecha.get(fecha, 0) + 1

        obj.Sesiones = {
            "Cantidad": len(sesiones),
            "Dispositivos": sorted({sesion.Dispositivo for sesion in sesiones}),
            "Ips": sorted({sesion.IpConexion for sesion in sesiones}),
            "FechasConexion": [
                {"Fecha": fecha, "Cantidad": cantidad}
                for fecha, cantidad in sorted(
                    conexiones_por_fecha.items(),
                    key=lambda item: datetime.strptime(item[0], "%d/%m/%Y"),
                )
            ],
            "SesionesActivas": [
                {
                    "Dispositivo": sesion.Dispositivo,
                    "Ip": sesion.IpConexion,
                    "FechaConexion": formatear_fecha_larga(sesion.FechaConexion),
                    "Movil": "Si" if sesion.EsMovil else "No",
                }
                for sesion in sesiones
                if sesion.Activa
            ],
        }

        return obj