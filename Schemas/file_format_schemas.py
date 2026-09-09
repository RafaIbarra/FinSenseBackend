from datetime import date, datetime
from pydantic import BaseModel, field_serializer


class ExcelIvaFormat(BaseModel):

    NombreEmpresa: str
    NumeroRuc: str
    TotalGasto: int
    IvaDiez: int
    IvaCinco: int
    FechaFactura: date
    TipoRegistro: str
    NumeroFactura: str
    Categoria: str
    FechaRegistro: datetime

    @field_serializer("FechaFactura")
    def serialize_fecha_factura(self, value: date) -> str:
        return value.strftime("%d/%m/%Y")

    @field_serializer("FechaRegistro")
    def serialize_fecha_registro(self, value: datetime) -> str:
        return value.strftime("%d/%m/%Y %H:%M:%S")