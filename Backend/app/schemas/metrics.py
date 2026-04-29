from datetime import datetime

from pydantic import BaseModel, Field


class RegistroVisitaPayload(BaseModel):
    visitor_id: str = Field(..., min_length=12, max_length=180)
    path: str = Field(default="/", max_length=240)


class RegistroVisitaResponse(BaseModel):
    accepted: bool = True


class PedidosMetricasFiltrosAplicados(BaseModel):
    rango: str
    group_by: str
    fecha_desde: datetime | None
    fecha_hasta: datetime | None
    estados: list[str] = Field(default_factory=list)
    paises: list[str] = Field(default_factory=list)
    producto_ids: list[int] = Field(default_factory=list)
    categoria_ids: list[int] = Field(default_factory=list)
    min_total: float | None
    max_total: float | None
    top_n: int
    ventas_solo_aprobadas: bool


class PedidosMetricasResumen(BaseModel):
    total_generado: float
    total_pendiente: float
    total_rechazado: float
    total_pedidos: int
    pedidos_pagados: int
    pedidos_pendientes: int
    pedidos_rechazados: int
    unidades_vendidas: int
    ticket_promedio_pagado: float
    tasa_aprobacion: float


class PedidosMetricasEstadoItem(BaseModel):
    estado: str
    etiqueta: str
    cantidad_pedidos: int
    monto_total: float
    participacion_pedidos: float
    participacion_monto: float


class PedidosMetricasTendenciaItem(BaseModel):
    periodo: str
    cantidad_pedidos: int
    total_generado: float
    total_pendiente: float
    total_rechazado: float


class PedidosMetricasProductoItem(BaseModel):
    producto_id: int
    producto_nombre: str
    unidades: int
    ingresos: float
    participacion_unidades: float
    participacion_ingresos: float


class PedidosMetricasCategoriaItem(BaseModel):
    categoria_id: int
    categoria_nombre: str
    producto_id: int
    producto_nombre: str
    unidades: int
    ingresos: float
    participacion_unidades: float
    participacion_ingresos: float


class PedidosMetricasPaisItem(BaseModel):
    pais: str
    cantidad_pedidos: int
    monto_total: float
    participacion_pedidos: float


class PedidosMetricasPerformance(BaseModel):
    cached: bool
    generated_at: datetime
    cache_ttl_seconds: int


class VisitantesMetricasResumen(BaseModel):
    total_visitas: int
    visitantes_unicos_aprox: int
    visitas_hoy: int
    visitantes_hoy_aprox: int
    rango_dias_considerado: int
    rango_recortado: bool = False
    disponible: bool = True
    fuente: str = "redis_hll"


class PedidosMetricasResponse(BaseModel):
    filtros: PedidosMetricasFiltrosAplicados
    resumen: PedidosMetricasResumen
    visitantes: VisitantesMetricasResumen
    estado_breakdown: list[PedidosMetricasEstadoItem] = Field(default_factory=list)
    tendencia: list[PedidosMetricasTendenciaItem] = Field(default_factory=list)
    top_productos: list[PedidosMetricasProductoItem] = Field(default_factory=list)
    top_categorias: list[PedidosMetricasCategoriaItem] = Field(default_factory=list)
    top_paises: list[PedidosMetricasPaisItem] = Field(default_factory=list)
    performance: PedidosMetricasPerformance
