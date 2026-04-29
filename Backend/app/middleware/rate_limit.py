import time
from collections import defaultdict, deque
from typing import Callable

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.config import settings
from app.utils.cache import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._local_store: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        if settings.rate_limit_trust_x_forwarded_for:
            xff = request.headers.get("x-forwarded-for")
            if xff:
                first_hop = xff.split(",")[0].strip()
                if first_hop:
                    return first_hop

        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    def _local_hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds
        bucket = self._local_store[key]

        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, int(bucket[0] + window_seconds - now))
            return False, retry_after

        bucket.append(now)
        return True, 0

    def _redis_hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        client = get_redis_client()
        if client is None:
            return self._local_hit(key, limit, window_seconds)

        current = client.incr(key)
        if current == 1:
            client.expire(key, window_seconds)

        if current > limit:
            ttl = client.ttl(key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            return False, retry_after

        return True, 0

    async def dispatch(self, request: Request, call_next: Callable):
        if not settings.rate_limit_enabled:
            return await call_next(request)

        ip = self._client_ip(request)
        path = request.url.path
        normalized_path = path.rstrip("/") or "/"

        global_window = int(time.time() // settings.rate_limit_global_window_seconds)
        global_key = f"rl:global:{ip}:{global_window}"
        allowed, retry_after = self._redis_hit(
            global_key,
            settings.rate_limit_global_requests,
            settings.rate_limit_global_window_seconds,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit excedido. Intenta de nuevo en unos segundos."},
                headers={"Retry-After": str(retry_after)},
            )

        if normalized_path == "/auth/login":
            login_window = int(time.time() // settings.rate_limit_login_window_seconds)
            login_key = f"rl:login:{ip}:{login_window}"
            allowed, retry_after = self._redis_hit(
                login_key,
                settings.rate_limit_login_requests,
                settings.rate_limit_login_window_seconds,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiados intentos de login. Espera e intenta de nuevo."},
                    headers={"Retry-After": str(retry_after)},
                )

        if normalized_path == "/pedidos" and request.method == "POST":
            order_window = int(time.time() // settings.rate_limit_create_order_window_seconds)
            order_key = f"rl:create_order:{ip}:{order_window}"
            allowed, retry_after = self._redis_hit(
                order_key,
                settings.rate_limit_create_order_requests,
                settings.rate_limit_create_order_window_seconds,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiados intentos de crear pedido. Espera e intenta de nuevo."},
                    headers={"Retry-After": str(retry_after)},
                )

        if normalized_path == "/payments/create" and request.method == "POST":
            payment_create_window = int(time.time() // settings.rate_limit_create_payment_window_seconds)
            payment_create_key = f"rl:create_payment:{ip}:{payment_create_window}"
            allowed, retry_after = self._redis_hit(
                payment_create_key,
                settings.rate_limit_create_payment_requests,
                settings.rate_limit_create_payment_window_seconds,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiados intentos de crear pago. Espera e intenta de nuevo."},
                    headers={"Retry-After": str(retry_after)},
                )

        if normalized_path.startswith("/payments/") and request.method == "GET":
            payment_get_window = int(time.time() // settings.rate_limit_get_payment_window_seconds)
            payment_get_key = f"rl:get_payment:{ip}:{payment_get_window}"
            allowed, retry_after = self._redis_hit(
                payment_get_key,
                settings.rate_limit_get_payment_requests,
                settings.rate_limit_get_payment_window_seconds,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiadas consultas de estado de pago. Espera e intenta de nuevo."},
                    headers={"Retry-After": str(retry_after)},
                )

        if normalized_path == "/pedidos/metricas/visitas/register" and request.method == "POST":
            visit_window_seconds = 60
            visit_window = int(time.time() // visit_window_seconds)
            visit_key = f"rl:visit:{ip}:{visit_window}"
            allowed, retry_after = self._redis_hit(
                visit_key,
                limit=30,
                window_seconds=visit_window_seconds,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Demasiados eventos de visita. Espera e intenta de nuevo."},
                    headers={"Retry-After": str(retry_after)},
                )

        return await call_next(request)
