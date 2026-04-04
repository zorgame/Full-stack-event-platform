from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import string

import bcrypt
from jose import jwt

from app.core.config import settings


def _normalizar_password(password: str) -> str:
	password_bytes = password.encode("utf-8")
	if len(password_bytes) <= 72:
		return password

	return f"sha256${hashlib.sha256(password_bytes).hexdigest()}"


def _password_bytes(password: str) -> bytes:
	return _normalizar_password(password).encode("utf-8")


def verificar_password(plain_password: str, hashed_password: str) -> bool:
	try:
		hashed = str(hashed_password or "").encode("utf-8")
		if not hashed:
			return False
		return bool(bcrypt.checkpw(_password_bytes(plain_password), hashed))
	except Exception:
		return False


def generar_hash_password(password: str) -> str:
	hashed = bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt(rounds=12))
	return hashed.decode("utf-8")


def crear_access_token(
	*,
	sub: str,
	expires_delta: timedelta | None = None,
) -> str:
	if expires_delta is None:
		expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

	expire = datetime.now(timezone.utc) + expires_delta
	payload = {"sub": sub, "exp": expire}
	encoded_jwt = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
	return encoded_jwt


def generar_password_segura(longitud: int = 20) -> str:
	longitud_normalizada = max(12, int(longitud or 20))
	alfabeto = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"

	base = [
		secrets.choice(string.ascii_lowercase),
		secrets.choice(string.ascii_uppercase),
		secrets.choice(string.digits),
		secrets.choice("!@#$%^&*()-_=+"),
	]

	while len(base) < longitud_normalizada:
		base.append(secrets.choice(alfabeto))

	secrets.SystemRandom().shuffle(base)
	return "".join(base)
