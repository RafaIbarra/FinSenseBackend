import enum

from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import relationship

from Config.settings import Base


class TipoRegistroEnum(enum.Enum):
    Manual = "Manual"
    Automatico = "Automatico"
    Asistido = "Asistido"


class MovimientosGastos(Base):
    __tablename__ = "MovimientosGastos"
    

    Id = Column("Id", Integer, primary_key=True, index=True)
    FechaRegistro = Column("FechaRegistro", DateTime(timezone=True), server_default=func.now(), nullable=False)
    TotalGasto = Column("TotalGasto", Integer, nullable=False)
    IvaDiez = Column("IvaDiez", Integer, nullable=False)
    IvaCinco = Column("IvaCinco", Integer, nullable=False)
    FechaGasto = Column("FechaGasto", Date, nullable=False)
    TipoRegistro = Column("TipoRegistro", SQLEnum(TipoRegistroEnum, name="tiporegistroenum"), nullable=False)
    UsuarioId = Column("UsuarioId", Integer, ForeignKey("Usuarios.Id"), nullable=False, index=True)
    CategoriaId = Column("CategoriaId", Integer, ForeignKey("CategoriasGastos.Id"), nullable=False, index=True)
    EmpresaId = Column("EmpresaId", Integer, ForeignKey("Empresas.Id"), nullable=False, index=True)
    NumeroFactura = Column("NumeroFactura", String(255), nullable=True)
    ModeloExtraccionDatos = Column("ModeloExtraccionDatos", String(255), nullable=True)
    ModeloClasificador = Column("ModeloClasificador", String(255), nullable=True)

    usuario = relationship("Usuarios", back_populates="movimientos_gastos")
    categoria = relationship("CategoriasGastos", back_populates="movimientos_gastos")
    empresa = relationship("Empresas", back_populates="movimientos_gastos")
    imagenes_pendientes = relationship(
        "ImagenesPendientes",
        back_populates="movimiento",
    )
    imagenes = relationship(
        "MovimientosGastosImagenes",
        back_populates="movimiento_gasto",
        cascade="all, delete-orphan",
    )
    etiquetas = relationship(
        "MovimientosGastosEtiquetas",
        back_populates="movimiento_gasto",
        cascade="all, delete-orphan",
    )
    conceptos = relationship(
        "MovimientosGastosConceptos",
        back_populates="movimiento_gasto",
        cascade="all, delete-orphan",
    )
