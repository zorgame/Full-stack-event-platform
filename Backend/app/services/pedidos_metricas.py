from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.core import constants
from app.core.config import settings
from app.models import Categorias, DetallePedido, Pedidos, Productos
from app.schemas.metrics import (
    PedidosMetricasCategoriaItem,
    PedidosMetricasEstadoItem,
    PedidosMetricasFiltrosAplicados,
    PedidosMetricasPaisItem,
    PedidosMetricasPerformance,
    PedidosMetricasProductoItem,
    PedidosMetricasResponse,
    PedidosMetricasResumen,
    PedidosMetricasTendenciaItem,
)
from app.utils.cache import cache_get_json, cache_set_json


_ESTADOS_RECHAZADOS = {constants.PEDIDO_ESTADO_CANCELADO, constants.PEDIDO_ESTADO_FALLIDO}
_RANGOS_PERMITIDOS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "180d": 180,
    "365d": 365,
}
_GROUP_BY_PERMITIDOS = {"day", "week", "month"}
_TOP_N_MIN = 3
_TOP_N_MAX = 20


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _normalizar_texto(valor: str) -> str:
    return str(valor or "").strip().lower()


def _parse_csv_text(raw: str | None, *, max_items: int = 30) -> list[str]:
    if not raw:
        return []

    vistos: set[str] = set()
    values: list[str] = []
    for chunk in str(raw).split(","):
        valor = _normalizar_texto(chunk)
        if not valor or valor in vistos:
            continue
        vistos.add(valor)
        values.append(valor)
        if len(values) >= max_items:
            break

    return values


def _parse_csv_int(raw: str | None, *, max_items: int = 50) -> list[int]:
    if not raw:
        return []

    vistos: set[int] = set()
    values: list[int] = []
    for chunk in str(raw).split(","):
        match = re.search(r"\d+", chunk or "")
        if not match:
            continue

        numero = int(match.group(0))
        if numero <= 0 or numero in vistos:
            continue

        vistos.add(numero)
        values.append(numero)
        if len(values) >= max_items:
            break

    return values


def _parse_estados(raw: str | None) -> list[str]:
    candidatos = _parse_csv_text(raw, max_items=10)
    if not candidatos:
        return []

    invalidos = [estado for estado in candidatos if estado not in constants.PEDIDO_ESTADOS_VALIDOS]
    if invalidos:
        raise ValueError("Estado de pedido no válido")

    return candidatos


def _resolver_rango(
    *,
    rango: str,
    fecha_desde: datetime | None,
    fecha_hasta: datetime | None,
) -> tuple[datetime | None, datetime | None, str]:
    if fecha_desde and fecha_hasta:
        if fecha_desde > fecha_hasta:
            raise ValueError("La fecha inicial no puede ser mayor a la fecha final")
        return fecha_desde, fecha_hasta, "custom"

    if fecha_desde and not fecha_hasta:
        return fecha_desde, datetime.now(timezone.utc), "custom"

    if fecha_hasta and not fecha_desde:
        return fecha_hasta - timedelta(days=30), fecha_hasta, "custom"

    rango_normalizado = _normalizar_texto(rango) or "30d"
    now = datetime.now(timezone.utc)

    if rango_normalizado in _RANGOS_PERMITIDOS:
        dias = _RANGOS_PERMITIDOS[rango_normalizado]
        return now - timedelta(days=dias), now, rango_normalizado

    if rango_normalizado == "mtd":
        inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return inicio_mes, now, rango_normalizado

    if rango_normalizado == "qtd":
        mes_inicio = ((now.month - 1) // 3) * 3 + 1
        inicio_trimestre = now.replace(
            month=mes_inicio,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return inicio_trimestre, now, rango_normalizado

    if rango_normalizado == "ytd":
        inicio_anio = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return inicio_anio, now, rango_normalizado

    if rango_normalizado == "all":
        return None, None, rango_normalizado

    raise ValueError("Rango de fechas no válido")


def _expr_periodo(group_by: str):
    if group_by == "month":
        return func.date_format(Pedidos.fecha_creacion, "%Y-%m")
    if group_by == "week":
        return func.date_format(Pedidos.fecha_creacion, "%x-W%v")
    return func.date_format(Pedidos.fecha_creacion, "%Y-%m-%d")


def _label_estado(estado: str) -> str:
    if estado == constants.PEDIDO_ESTADO_PENDIENTE:
        return "Pendiente"
    if estado == constants.PEDIDO_ESTADO_PAGADO:
        return "Pagado"
    if estado == constants.PEDIDO_ESTADO_CANCELADO:
        return "Cancelado"
    if estado == constants.PEDIDO_ESTADO_FALLIDO:
        return "Fallido"
    return estado or "Sin estado"


def _build_order_scope_subquery(
    *,
    producto_ids: list[int],
    categoria_ids: list[int],
):
    if not producto_ids and not categoria_ids:
        return None

    stmt = select(DetallePedido.pedido_id).join(Categorias, DetallePedido.categoria_id == Categorias.id)

    if categoria_ids:
        stmt = stmt.where(DetallePedido.categoria_id.in_(tuple(categoria_ids)))
    if producto_ids:
        stmt = stmt.where(Categorias.producto_id.in_(tuple(producto_ids)))

    return stmt.distinct()


def _build_order_filters(
    *,
    fecha_desde: datetime | None,
    fecha_hasta: datetime | None,
    estados: list[str],
    paises: list[str],
    min_total: float | None,
    max_total: float | None,
    order_scope_subquery,
):
    filtros = []

    if fecha_desde is not None:
        filtros.append(Pedidos.fecha_creacion >= fecha_desde)
    if fecha_hasta is not None:
        filtros.append(Pedidos.fecha_creacion <= fecha_hasta)
    if estados:
        filtros.append(Pedidos.estado.in_(tuple(estados)))
    if paises:
        filtros.append(func.lower(func.trim(Pedidos.pais)).in_(tuple(paises)))
    if min_total is not None:
        filtros.append(Pedidos.total >= min_total)
    if max_total is not None:
        filtros.append(Pedidos.total <= max_total)
    if order_scope_subquery is not None:
        filtros.append(Pedidos.id.in_(order_scope_subquery))

    return filtros


def _build_detail_filters(
    *,
    order_filters,
    producto_ids: list[int],
    categoria_ids: list[int],
    ventas_solo_aprobadas: bool,
):
    filtros = list(order_filters)

    if ventas_solo_aprobadas:
        filtros.append(Pedidos.estado == constants.PEDIDO_ESTADO_PAGADO)

    if categoria_ids:
        filtros.append(DetallePedido.categoria_id.in_(tuple(categoria_ids)))
    if producto_ids:
        filtros.append(Categorias.producto_id.in_(tuple(producto_ids)))

    return filtros


def _build_cache_key(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return f"{constants.CACHE_KEY_PEDIDOS_METRICAS_PREFIX}v1:{digest}"


def _metricas_ttl_seconds() -> int:
    return min(max(int(settings.cache_default_ttl_seconds // 2 or 90), 60), 300)


def obtener_metricas_pedidos(
    db: Session,
    *,
    rango: str = "30d",
    fecha_desde: datetime | None = None,
    fecha_hasta: datetime | None = None,
    group_by: str = "day",
    estado: str | None = None,
    pais: str | None = None,
    producto_ids: str | None = None,
    categoria_ids: str | None = None,
    min_total: float | None = None,
    max_total: float | None = None,
    top_n: int = 8,
    ventas_solo_aprobadas: bool = True,
) -> PedidosMetricasResponse:
    if min_total is not None and max_total is not None and min_total > max_total:
        raise ValueError("El monto mínimo no puede ser mayor al monto máximo")

    group_by_normalizado = _normalizar_texto(group_by) or "day"
    if group_by_normalizado not in _GROUP_BY_PERMITIDOS:
        raise ValueError("Agrupación temporal no válida")

    top_n_normalizado = max(_TOP_N_MIN, min(_TOP_N_MAX, int(top_n or 8)))

    estados = _parse_estados(estado)
    paises = _parse_csv_text(pais, max_items=20)
    producto_ids_list = _parse_csv_int(producto_ids, max_items=50)
    categoria_ids_list = _parse_csv_int(categoria_ids, max_items=100)

    fecha_desde_final, fecha_hasta_final, rango_aplicado = _resolver_rango(
        rango=rango,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    order_scope_subquery = _build_order_scope_subquery(
        producto_ids=producto_ids_list,
        categoria_ids=categoria_ids_list,
    )

    order_filters = _build_order_filters(
        fecha_desde=fecha_desde_final,
        fecha_hasta=fecha_hasta_final,
        estados=estados,
        paises=paises,
        min_total=min_total,
        max_total=max_total,
        order_scope_subquery=order_scope_subquery,
    )

    detail_filters = _build_detail_filters(
        order_filters=order_filters,
        producto_ids=producto_ids_list,
        categoria_ids=categoria_ids_list,
        ventas_solo_aprobadas=ventas_solo_aprobadas,
    )

    cache_key_payload = {
        "rango": rango_aplicado,
        "fecha_desde": fecha_desde_final.isoformat() if fecha_desde_final else None,
        "fecha_hasta": fecha_hasta_final.isoformat() if fecha_hasta_final else None,
        "group_by": group_by_normalizado,
        "estados": sorted(estados),
        "paises": sorted(paises),
        "producto_ids": sorted(producto_ids_list),
        "categoria_ids": sorted(categoria_ids_list),
        "min_total": min_total,
        "max_total": max_total,
        "top_n": top_n_normalizado,
        "ventas_solo_aprobadas": bool(ventas_solo_aprobadas),
    }
    cache_ttl_seconds = _metricas_ttl_seconds()
    cache_key = _build_cache_key(cache_key_payload)

    cached = cache_get_json(cache_key)
    if cached is not None:
        payload = PedidosMetricasResponse.model_validate(cached)
        payload.performance.cached = True
        payload.performance.cache_ttl_seconds = cache_ttl_seconds
        return payload

    resumen_stmt = select(
        func.coalesce(
            func.sum(
                case((Pedidos.estado == constants.PEDIDO_ESTADO_PAGADO, Pedidos.total), else_=0)
            ),
            0,
        ).label("total_generado"),
        func.coalesce(
            func.sum(
                case((Pedidos.estado == constants.PEDIDO_ESTADO_PENDIENTE, Pedidos.total), else_=0)
            ),
            0,
        ).label("total_pendiente"),
        func.coalesce(
            func.sum(
                case((Pedidos.estado.in_(tuple(_ESTADOS_RECHAZADOS)), Pedidos.total), else_=0)
            ),
            0,
        ).label("total_rechazado"),
        func.count(Pedidos.id).label("total_pedidos"),
        func.coalesce(
            func.sum(case((Pedidos.estado == constants.PEDIDO_ESTADO_PAGADO, 1), else_=0)),
            0,
        ).label("pedidos_pagados"),
        func.coalesce(
            func.sum(case((Pedidos.estado == constants.PEDIDO_ESTADO_PENDIENTE, 1), else_=0)),
            0,
        ).label("pedidos_pendientes"),
        func.coalesce(
            func.sum(case((Pedidos.estado.in_(tuple(_ESTADOS_RECHAZADOS)), 1), else_=0)),
            0,
        ).label("pedidos_rechazados"),
    ).where(*order_filters)
    resumen_row = db.execute(resumen_stmt).mappings().one()

    unidades_stmt = (
        select(func.coalesce(func.sum(DetallePedido.cantidad), 0).label("unidades_vendidas"))
        .select_from(DetallePedido)
        .join(Pedidos, DetallePedido.pedido_id == Pedidos.id)
        .join(Categorias, DetallePedido.categoria_id == Categorias.id)
        .where(*detail_filters)
    )
    unidades_row = db.execute(unidades_stmt).mappings().one()

    total_generado = _to_float(resumen_row["total_generado"])
    pedidos_pagados = _to_int(resumen_row["pedidos_pagados"])
    unidades_vendidas = _to_int(unidades_row["unidades_vendidas"])

    ticket_promedio_pagado = total_generado / pedidos_pagados if pedidos_pagados > 0 else 0.0
    tasa_aprobacion = (
        (pedidos_pagados / max(_to_int(resumen_row["total_pedidos"]), 1)) * 100
        if _to_int(resumen_row["total_pedidos"]) > 0
        else 0.0
    )

    resumen = PedidosMetricasResumen(
        total_generado=total_generado,
        total_pendiente=_to_float(resumen_row["total_pendiente"]),
        total_rechazado=_to_float(resumen_row["total_rechazado"]),
        total_pedidos=_to_int(resumen_row["total_pedidos"]),
        pedidos_pagados=pedidos_pagados,
        pedidos_pendientes=_to_int(resumen_row["pedidos_pendientes"]),
        pedidos_rechazados=_to_int(resumen_row["pedidos_rechazados"]),
        unidades_vendidas=unidades_vendidas,
        ticket_promedio_pagado=ticket_promedio_pagado,
        tasa_aprobacion=tasa_aprobacion,
    )

    estado_stmt = (
        select(
            Pedidos.estado.label("estado"),
            func.count(Pedidos.id).label("cantidad_pedidos"),
            func.coalesce(func.sum(Pedidos.total), 0).label("monto_total"),
        )
        .where(*order_filters)
        .group_by(Pedidos.estado)
    )
    estado_rows = db.execute(estado_stmt).mappings().all()

    total_pedidos = max(resumen.total_pedidos, 1)
    total_monto = max(
        resumen.total_generado + resumen.total_pendiente + resumen.total_rechazado,
        0.000001,
    )

    estado_breakdown: list[PedidosMetricasEstadoItem] = []
    for row in estado_rows:
        monto = _to_float(row["monto_total"])
        cantidad = _to_int(row["cantidad_pedidos"])
        estado_valor = str(row["estado"] or "")
        estado_breakdown.append(
            PedidosMetricasEstadoItem(
                estado=estado_valor,
                etiqueta=_label_estado(estado_valor),
                cantidad_pedidos=cantidad,
                monto_total=monto,
                participacion_pedidos=(cantidad / total_pedidos) * 100,
                participacion_monto=(monto / total_monto) * 100,
            )
        )

    periodo_expr = _expr_periodo(group_by_normalizado)
    max_puntos = 180 if group_by_normalizado in {"week", "month"} else 120

    tendencia_stmt = (
        select(
            periodo_expr.label("periodo"),
            func.count(Pedidos.id).label("cantidad_pedidos"),
            func.coalesce(
                func.sum(
                    case((Pedidos.estado == constants.PEDIDO_ESTADO_PAGADO, Pedidos.total), else_=0)
                ),
                0,
            ).label("total_generado"),
            func.coalesce(
                func.sum(
                    case((Pedidos.estado == constants.PEDIDO_ESTADO_PENDIENTE, Pedidos.total), else_=0)
                ),
                0,
            ).label("total_pendiente"),
            func.coalesce(
                func.sum(
                    case((Pedidos.estado.in_(tuple(_ESTADOS_RECHAZADOS)), Pedidos.total), else_=0)
                ),
                0,
            ).label("total_rechazado"),
        )
        .where(*order_filters)
        .group_by(periodo_expr)
        .order_by(desc(periodo_expr))
        .limit(max_puntos)
    )
    tendencia_rows = list(reversed(db.execute(tendencia_stmt).mappings().all()))

    tendencia = [
        PedidosMetricasTendenciaItem(
            periodo=str(row["periodo"] or ""),
            cantidad_pedidos=_to_int(row["cantidad_pedidos"]),
            total_generado=_to_float(row["total_generado"]),
            total_pendiente=_to_float(row["total_pendiente"]),
            total_rechazado=_to_float(row["total_rechazado"]),
        )
        for row in tendencia_rows
    ]

    unidades_por_producto_expr = func.coalesce(func.sum(DetallePedido.cantidad), 0)
    ingresos_por_producto_expr = func.coalesce(func.sum(DetallePedido.subtotal), 0)

    top_productos_stmt = (
        select(
            Productos.id.label("producto_id"),
            Productos.nombre.label("producto_nombre"),
            unidades_por_producto_expr.label("unidades"),
            ingresos_por_producto_expr.label("ingresos"),
        )
        .select_from(DetallePedido)
        .join(Pedidos, DetallePedido.pedido_id == Pedidos.id)
        .join(Categorias, DetallePedido.categoria_id == Categorias.id)
        .join(Productos, Categorias.producto_id == Productos.id)
        .where(*detail_filters)
        .group_by(Productos.id, Productos.nombre)
        .order_by(desc(unidades_por_producto_expr), desc(ingresos_por_producto_expr))
        .limit(top_n_normalizado)
    )
    top_productos_rows = db.execute(top_productos_stmt).mappings().all()

    total_unidades_top_productos = max(sum(_to_int(item["unidades"]) for item in top_productos_rows), 1)
    total_ingresos_top_productos = max(sum(_to_float(item["ingresos"]) for item in top_productos_rows), 0.000001)

    top_productos = [
        PedidosMetricasProductoItem(
            producto_id=_to_int(item["producto_id"]),
            producto_nombre=str(item["producto_nombre"] or "Producto sin nombre"),
            unidades=_to_int(item["unidades"]),
            ingresos=_to_float(item["ingresos"]),
            participacion_unidades=(_to_int(item["unidades"]) / total_unidades_top_productos) * 100,
            participacion_ingresos=(_to_float(item["ingresos"]) / total_ingresos_top_productos) * 100,
        )
        for item in top_productos_rows
    ]

    unidades_por_categoria_expr = func.coalesce(func.sum(DetallePedido.cantidad), 0)
    ingresos_por_categoria_expr = func.coalesce(func.sum(DetallePedido.subtotal), 0)

    top_categorias_stmt = (
        select(
            Categorias.id.label("categoria_id"),
            Categorias.nombre.label("categoria_nombre"),
            Productos.id.label("producto_id"),
            Productos.nombre.label("producto_nombre"),
            unidades_por_categoria_expr.label("unidades"),
            ingresos_por_categoria_expr.label("ingresos"),
        )
        .select_from(DetallePedido)
        .join(Pedidos, DetallePedido.pedido_id == Pedidos.id)
        .join(Categorias, DetallePedido.categoria_id == Categorias.id)
        .join(Productos, Categorias.producto_id == Productos.id)
        .where(*detail_filters)
        .group_by(Categorias.id, Categorias.nombre, Productos.id, Productos.nombre)
        .order_by(desc(unidades_por_categoria_expr), desc(ingresos_por_categoria_expr))
        .limit(top_n_normalizado)
    )
    top_categorias_rows = db.execute(top_categorias_stmt).mappings().all()

    total_unidades_top_categorias = max(sum(_to_int(item["unidades"]) for item in top_categorias_rows), 1)
    total_ingresos_top_categorias = max(sum(_to_float(item["ingresos"]) for item in top_categorias_rows), 0.000001)

    top_categorias = [
        PedidosMetricasCategoriaItem(
            categoria_id=_to_int(item["categoria_id"]),
            categoria_nombre=str(item["categoria_nombre"] or "Categoría sin nombre"),
            producto_id=_to_int(item["producto_id"]),
            producto_nombre=str(item["producto_nombre"] or "Producto sin nombre"),
            unidades=_to_int(item["unidades"]),
            ingresos=_to_float(item["ingresos"]),
            participacion_unidades=(_to_int(item["unidades"]) / total_unidades_top_categorias) * 100,
            participacion_ingresos=(_to_float(item["ingresos"]) / total_ingresos_top_categorias) * 100,
        )
        for item in top_categorias_rows
    ]

    pais_expr = func.coalesce(func.nullif(func.trim(Pedidos.pais), ""), "Sin país")
    top_paises_stmt = (
        select(
            pais_expr.label("pais"),
            func.count(Pedidos.id).label("cantidad_pedidos"),
            func.coalesce(func.sum(Pedidos.total), 0).label("monto_total"),
        )
        .where(*order_filters)
        .group_by(pais_expr)
        .order_by(desc(func.count(Pedidos.id)), desc(func.coalesce(func.sum(Pedidos.total), 0)))
        .limit(min(max(top_n_normalizado, 5), 15))
    )
    top_paises_rows = db.execute(top_paises_stmt).mappings().all()

    total_pedidos_paises = max(sum(_to_int(item["cantidad_pedidos"]) for item in top_paises_rows), 1)
    top_paises = [
        PedidosMetricasPaisItem(
            pais=str(item["pais"] or "Sin país"),
            cantidad_pedidos=_to_int(item["cantidad_pedidos"]),
            monto_total=_to_float(item["monto_total"]),
            participacion_pedidos=(_to_int(item["cantidad_pedidos"]) / total_pedidos_paises) * 100,
        )
        for item in top_paises_rows
    ]

    response = PedidosMetricasResponse(
        filtros=PedidosMetricasFiltrosAplicados(
            rango=rango_aplicado,
            group_by=group_by_normalizado,
            fecha_desde=fecha_desde_final,
            fecha_hasta=fecha_hasta_final,
            estados=estados,
            paises=paises,
            producto_ids=producto_ids_list,
            categoria_ids=categoria_ids_list,
            min_total=min_total,
            max_total=max_total,
            top_n=top_n_normalizado,
            ventas_solo_aprobadas=bool(ventas_solo_aprobadas),
        ),
        resumen=resumen,
        estado_breakdown=estado_breakdown,
        tendencia=tendencia,
        top_productos=top_productos,
        top_categorias=top_categorias,
        top_paises=top_paises,
        performance=PedidosMetricasPerformance(
            cached=False,
            generated_at=datetime.now(timezone.utc),
            cache_ttl_seconds=cache_ttl_seconds,
        ),
    )

    cache_set_json(cache_key, response.model_dump(mode="json"), cache_ttl_seconds)
    return response
