import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


logger = logging.getLogger("tickets_api")


class LoggingMiddleware(BaseHTTPMiddleware):
	def __init__(self, app: ASGIApp) -> None:
		super().__init__(app)

	async def dispatch(self, request: Request, call_next: Callable):
		inicio = time.perf_counter()
		response = await call_next(request)
		duracion_ms = (time.perf_counter() - inicio) * 1000

		logger.info(
			"%s %s - %s - %.2fms",
			request.method,
			request.url.path,
			response.status_code,
			duracion_ms,
		)

		return response
