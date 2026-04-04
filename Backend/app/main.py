import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from app.api.routes import auth, categorias, payments, pedidos, productos, usuarios
from app.core.config import settings
from app.db.session import engine
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.utils.cache import get_redis_client
from app.utils.media import ensure_media_directories

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(_: FastAPI):
	try:
		with engine.connect() as connection:
			connection.execute(text("SELECT 1"))
		logger.info("Base de datos conectada correctamente")
	except Exception as exc:
		logger.warning("No se pudo conectar a la base de datos: %s", exc)

	redis_client = get_redis_client()
	if redis_client is not None:
		logger.info("Redis conectado correctamente")
	else:
		logger.warning("Redis no disponible; la API seguirá sin cache")

	yield


def create_app() -> FastAPI:
	app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
	ensure_media_directories()
	app.mount(
		settings.normalized_media_url_path,
		StaticFiles(directory=str(settings.media_root_path)),
		name="media",
	)

	app.add_middleware(SecurityHeadersMiddleware)
	app.add_middleware(RequestIdMiddleware)
	app.add_middleware(RateLimitMiddleware)
	app.add_middleware(LoggingMiddleware)

	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.normalized_allowed_origins,
		allow_origin_regex=(str(settings.cors_allow_origin_regex or "").strip() or None),
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	if settings.gzip_enabled:
		app.add_middleware(
			GZipMiddleware,
			minimum_size=max(100, int(settings.gzip_minimum_size_bytes)),
			compresslevel=max(1, min(9, int(settings.gzip_compresslevel))),
		)

	app.include_router(auth.router)
	app.include_router(usuarios.router)
	app.include_router(categorias.router)
	app.include_router(productos.router)
	app.include_router(pedidos.router)
	app.include_router(payments.router)

	@app.get("/health")
	async def health_check():
		db_ok = False
		redis_ok = False

		try:
			with engine.connect() as connection:
				connection.execute(text("SELECT 1"))
			db_ok = True
		except Exception:
			db_ok = False

		try:
			redis = get_redis_client()
			if redis is not None:
				redis.ping()
				redis_ok = True
		except Exception:
			redis_ok = False

		status_code = 200 if db_ok else 503
		return JSONResponse(
			status_code=status_code,
			content={
				"status": "ok" if db_ok else "degraded",
				"database": "ok" if db_ok else "error",
				"redis": "ok" if redis_ok else "unavailable",
			},
		)

	@app.exception_handler(Exception)
	async def unhandled_exception_handler(request: Request, exc: Exception):
		logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
		return JSONResponse(
			status_code=500,
			content={"detail": "Error interno del servidor"},
		)

	return app


app = create_app()

