import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

class RequestIdMiddleware(BaseHTTPMiddleware):

	def __init__(self, app: ASGIApp) -> None:
		super().__init__(app)

	async def dispatch(self, request: Request, call_next: Callable):
		request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
		request.state.request_id = request_id

		response = await call_next(request)
		response.headers["X-Request-ID"] = request_id
		return response
