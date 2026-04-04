from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoriaBase(BaseModel):
    producto_id: int
    nombre: str = Field(..., max_length=120)
    descripcion: str | None = None
    precio: Decimal = Field(..., gt=0)
    moneda: str = Field("USD", min_length=3, max_length=3)
    unidades_disponibles: int = Field(..., ge=0)
    limite_por_usuario: int | None = Field(default=None, ge=1)
    activo: bool = True
    is_active: bool = True


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaCreateEnProducto(BaseModel):
    nombre: str = Field(..., max_length=120)
    descripcion: str | None = None
    precio: Decimal = Field(..., gt=0)
    moneda: str = Field("USD", min_length=3, max_length=3)
    unidades_disponibles: int = Field(..., ge=0)
    limite_por_usuario: int | None = Field(default=None, ge=1)
    activo: bool = True
    is_active: bool = True


class CategoriaUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=120)
    descripcion: str | None = None
    precio: Decimal | None = Field(default=None, gt=0)
    moneda: str | None = Field(default=None, min_length=3, max_length=3)
    unidades_disponibles: int | None = Field(default=None, ge=0)
    limite_por_usuario: int | None = Field(default=None, ge=1)
    activo: bool | None = None
    is_active: bool | None = None


class CategoriaResponse(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProductoBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    fecha: datetime | None = None
    ubicacion: str = Field(..., max_length=255)
    estadio: str | None = Field(default=None, max_length=255)
    ubicacion_estadio: str | None = Field(default=None, max_length=255)
    descripcion: str | None = None
    imagen: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class ProductoCreate(ProductoBase):
    categorias: list[CategoriaCreateEnProducto] = Field(default_factory=list)


class ProductoUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=255)
    fecha: datetime | None = None
    ubicacion: str | None = Field(default=None, max_length=255)
    estadio: str | None = Field(default=None, max_length=255)
    ubicacion_estadio: str | None = Field(default=None, max_length=255)
    descripcion: str | None = None
    imagen: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class ProductoResponse(ProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    categorias: list[CategoriaResponse] = Field(default_factory=list)


class ProductoImagenUploadResponse(BaseModel):
    imagen: str
    url: str


class DetallePedidoBase(BaseModel):
    categoria_id: int
    cantidad: int = Field(..., gt=0)


class DetallePedidoCreate(DetallePedidoBase):
    pass


class DetallePedidoResponse(DetallePedidoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    precio_unitario: Decimal
    subtotal: Decimal
    created_at: datetime
    categoria: CategoriaResponse

class PedidoCreate(BaseModel):
    correo_electronico: str = Field(..., max_length=255)
    nombre_completo: str = Field(..., max_length=180)
    telefono: str = Field(..., max_length=60)
    pais: str = Field(..., max_length=120)
    documento: str = Field(..., max_length=80)
    acepta_terminos: bool = Field(...)
    detalles: list[DetallePedidoCreate] = Field(default_factory=list)


class PedidoEstadoUpdate(BaseModel):
    estado: str = Field(..., max_length=50)
    usuario_id: int | None = Field(default=None, ge=1)


class PedidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    referencia: str
    estado: str
    usuario_id: int | None
    total: Decimal
    correo_electronico: str | None
    nombre_completo: str | None
    telefono: str | None
    pais: str | None
    documento: str | None
    fecha_creacion: datetime
    detalles: list[DetallePedidoResponse] = Field(default_factory=list)