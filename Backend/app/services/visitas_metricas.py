from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, timedelta, timezone

from app.core import constants
from app.schemas.metrics import VisitantesMetricasResumen
from app.utils.cache import get_redis_client


logger = logging.getLogger("uvicorn.error")

_VISITAS_RETENTION_DAYS = 400
_VISITAS_DEDUP_SECONDS = 900
_VISITAS_MAX_RANGE_DAYS = 400
_VISITOR_ID_MIN_LENGTH = 12


def _normalizar_visitor_id(raw: str) -> str:
    text = str(raw or "").strip()
    if len(text) < _VISITOR_ID_MIN_LENGTH:
        return ""

    safe = "".join(ch for ch in text if ch.isalnum() or ch in {"-", "_", "."})
    if len(safe) < _VISITOR_ID_MIN_LENGTH:
        return ""

    return hashlib.sha1(safe.encode("utf-8")).hexdigest()


def _normalizar_path(raw: str | None) -> str:
    text = str(raw or "/").strip()
    if not text:
        return "/"

    text = text.split("?", 1)[0].split("#", 1)[0]
    if not text.startswith("/"):
        text = f"/{text}"

    parts = [chunk for chunk in text.split("/") if chunk]
    normalized = f"/{'/'.join(parts)}" if parts else "/"
    return normalized[:160]


def _day_token(value: date) -> str:
    return value.strftime("%Y%m%d")


def _hits_day_key(day_token: str) -> str:
    return f"{constants.CACHE_KEY_VISITAS_HITS_DAY_PREFIX}{day_token}"


def _unique_day_key(day_token: str) -> str:
    return f"{constants.CACHE_KEY_VISITAS_UNIQUE_DAY_PREFIX}{day_token}"


def _dedup_key(*, day_token: str, visitor_hash: str, path_hash: str) -> str:
    return f"{constants.CACHE_KEY_VISITAS_DEDUP_PREFIX}{day_token}:{visitor_hash}:{path_hash}"


def _as_utc_date(value: datetime | None) -> date | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.date()

    return value.astimezone(timezone.utc).date()


def _iter_day_tokens(start_date: date, end_date: date) -> tuple[list[str], bool]:
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    span_days = (end_date - start_date).days + 1
    was_clipped = False

    if span_days > _VISITAS_MAX_RANGE_DAYS:
        start_date = end_date - timedelta(days=_VISITAS_MAX_RANGE_DAYS - 1)
        span_days = _VISITAS_MAX_RANGE_DAYS
        was_clipped = True

    return [
        _day_token(start_date + timedelta(days=offset))
        for offset in range(span_days)
    ], was_clipped


def _to_int(raw) -> int:
    try:
        return int(raw or 0)
    except Exception:
        return 0


def registrar_visita(*, visitor_id: str, path: str | None = None) -> bool:
    client = get_redis_client()
    if client is None:
        return False

    visitor_hash = _normalizar_visitor_id(visitor_id)
    if not visitor_hash:
        return False

    normalized_path = _normalizar_path(path)
    path_hash = hashlib.sha1(normalized_path.encode("utf-8")).hexdigest()[:12]
    today_token = _day_token(datetime.now(timezone.utc).date())

    dedup_key = _dedup_key(
        day_token=today_token,
        visitor_hash=visitor_hash,
        path_hash=path_hash,
    )

    try:
        accepted = bool(client.set(dedup_key, "1", nx=True, ex=_VISITAS_DEDUP_SECONDS))
        if not accepted:
            return False

        day_hits_key = _hits_day_key(today_token)
        day_unique_key = _unique_day_key(today_token)

        pipe = client.pipeline(transaction=False)
        pipe.incr(day_hits_key)
        pipe.incr(constants.CACHE_KEY_VISITAS_HITS_ALL)
        pipe.pfadd(day_unique_key, visitor_hash)
        pipe.pfadd(constants.CACHE_KEY_VISITAS_UNIQUE_ALL, visitor_hash)
        pipe.expire(day_hits_key, _VISITAS_RETENTION_DAYS * 86400)
        pipe.expire(day_unique_key, _VISITAS_RETENTION_DAYS * 86400)
        pipe.execute()

        return True
    except Exception as exc:
        logger.warning("No fue posible registrar visita: %s", exc)
        return False


def obtener_resumen_visitas(
    *,
    fecha_desde: datetime | None,
    fecha_hasta: datetime | None,
) -> VisitantesMetricasResumen:
    client = get_redis_client()
    if client is None:
        return VisitantesMetricasResumen(
            total_visitas=0,
            visitantes_unicos_aprox=0,
            visitas_hoy=0,
            visitantes_hoy_aprox=0,
            rango_dias_considerado=0,
            rango_recortado=False,
            disponible=False,
            fuente="redis_unavailable",
        )

    today_token = _day_token(datetime.now(timezone.utc).date())
    today_hits_key = _hits_day_key(today_token)
    today_unique_key = _unique_day_key(today_token)

    try:
        visitas_hoy = _to_int(client.get(today_hits_key))
        visitantes_hoy_aprox = _to_int(client.pfcount(today_unique_key))

        # Caso historico completo: usa acumuladores all-time O(1).
        if fecha_desde is None and fecha_hasta is None:
            return VisitantesMetricasResumen(
                total_visitas=_to_int(client.get(constants.CACHE_KEY_VISITAS_HITS_ALL)),
                visitantes_unicos_aprox=_to_int(client.pfcount(constants.CACHE_KEY_VISITAS_UNIQUE_ALL)),
                visitas_hoy=visitas_hoy,
                visitantes_hoy_aprox=visitantes_hoy_aprox,
                rango_dias_considerado=0,
                rango_recortado=False,
                disponible=True,
                fuente="redis_hll",
            )

        start_date = _as_utc_date(fecha_desde)
        end_date = _as_utc_date(fecha_hasta)

        if start_date is None and end_date is None:
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=29)
        elif start_date is None:
            start_date = end_date - timedelta(days=29)
        elif end_date is None:
            end_date = datetime.now(timezone.utc).date()

        day_tokens, was_clipped = _iter_day_tokens(start_date, end_date)
        if not day_tokens:
            return VisitantesMetricasResumen(
                total_visitas=0,
                visitantes_unicos_aprox=0,
                visitas_hoy=visitas_hoy,
                visitantes_hoy_aprox=visitantes_hoy_aprox,
                rango_dias_considerado=0,
                rango_recortado=was_clipped,
                disponible=True,
                fuente="redis_hll",
            )

        hit_keys = [_hits_day_key(token) for token in day_tokens]
        unique_keys = [_unique_day_key(token) for token in day_tokens]

        hit_values = client.mget(hit_keys)
        total_visitas = sum(_to_int(value) for value in hit_values)
        visitantes_unicos_aprox = _to_int(client.pfcount(*unique_keys)) if unique_keys else 0

        return VisitantesMetricasResumen(
            total_visitas=total_visitas,
            visitantes_unicos_aprox=visitantes_unicos_aprox,
            visitas_hoy=visitas_hoy,
            visitantes_hoy_aprox=visitantes_hoy_aprox,
            rango_dias_considerado=len(day_tokens),
            rango_recortado=was_clipped,
            disponible=True,
            fuente="redis_hll",
        )
    except Exception as exc:
        logger.warning("No fue posible calcular resumen de visitas: %s", exc)
        return VisitantesMetricasResumen(
            total_visitas=0,
            visitantes_unicos_aprox=0,
            visitas_hoy=0,
            visitantes_hoy_aprox=0,
            rango_dias_considerado=0,
            rango_recortado=False,
            disponible=False,
            fuente="redis_error",
        )
