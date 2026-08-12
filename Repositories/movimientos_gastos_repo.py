from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Models.CategoriasGastos import CategoriasGastos
from Models.Empresas import Empresas
from Models.MovimientosGastos import MovimientosGastos


async def registrar(db: AsyncSession, movimiento: dict):
    """Registra o actualiza un movimiento de gasto.

    movimiento debe ser un diccionario con las claves:
    {id, user_id, total, iva_diez, iva_cinco, ruc, id_categoria, nro_factura, imagenes}
    """
    try:
        if not movimiento:
            return {"error": "Datos del movimiento no proporcionados"}

        ruc = movimiento.get("ruc")
        if not ruc:
            return {"error": "El RUC de la empresa es obligatorio"}

        empresa_result = await db.execute(select(Empresas).where(Empresas.Ruc == ruc))
        empresa = empresa_result.scalars().first()
        if not empresa:
            return {"error": f"Empresa con RUC {ruc} no encontrada"}

        movimiento_id = movimiento.get("id", 0) or 0
        imagenes = movimiento.get("imagenes", [])
        categoria_id = movimiento.get("id_categoria")
        usuario_id = movimiento.get("user_id")

        if not categoria_id:
            return {"error": "La categoría es obligatoria"}

        categoria_result = await db.execute(
            select(CategoriasGastos).where(
                CategoriasGastos.Id == categoria_id,
                CategoriasGastos.UsuarioId == usuario_id,
            )
        )
        categoria = categoria_result.scalars().first()
        if not categoria:
            return {"error": f"Categoría con id {categoria_id} no encontrada para el usuario"}

        if movimiento_id > 0:
            result = await db.execute(select(MovimientosGastos).where(MovimientosGastos.Id == movimiento_id))
            registro = result.scalars().first()
            if not registro:
                return {"error": f"Movimiento con id {movimiento_id} no encontrado"}

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
            return registro

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
        return nuevo_movimiento

    except Exception as e:
        await db.rollback()
        return {"error": str(e)}
