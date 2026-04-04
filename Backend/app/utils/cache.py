from __future__ import annotations

import json
import logging
import time
from typing import Any

import redis

from app.core.config import settings


_redis_client: redis.Redis | None = None
_redis_retry_after: float = 0.0
logger = logging.getLogger("uvicorn.error")


def get_redis_client() -> redis.Redis | None:
	global _redis_client
	global _redis_retry_after
	if _redis_client is not None:
		return _redis_client

	now = time.monotonic()
	if _redis_retry_after > now:
		return None

	try:
		_redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
		_redis_client.ping()
		_redis_retry_after = 0.0
		logger.info("Conexion inicial a Redis establecida")
		return _redis_client
	except Exception as exc:
		_retry_seconds = max(1, int(settings.redis_connect_retry_seconds or 30))
		_redis_retry_after = now + _retry_seconds
		logger.warning("Fallo la conexion a Redis: %s", exc)
		_redis_client = None
		return None


def cache_set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
	client = get_redis_client()
	if client is None:
		return

	payload = json.dumps(value, default=str)
	if ttl_seconds is None:
		client.set(key, payload)
	else:
		client.setex(key, ttl_seconds, payload)


def cache_get_json(key: str) -> Any | None:
	client = get_redis_client()
	if client is None:
		return None

	payload = client.get(key)
	if payload is None:
		return None
	try:
		return json.loads(payload)
	except json.JSONDecodeError:
		return None


def cache_delete(key: str) -> None:
	client = get_redis_client()
	if client is None:
		return
	client.delete(key)


def cache_delete_prefix(prefix: str) -> None:
	client = get_redis_client()
	if client is None or not prefix:
		return

	try:
		batch: list[str] = []
		for key in client.scan_iter(match=f"{prefix}*", count=200):
			batch.append(key)
			if len(batch) >= 200:
				client.delete(*batch)
				batch.clear()

		if batch:
			client.delete(*batch)
	except Exception as exc:
		logger.warning("No fue posible invalidar cache por prefijo '%s': %s", prefix, exc)
