from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")

        return response
