from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import usuarios as usuarios_repo
from app.api.dependencies.db import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
	token: str = Depends(oauth2_scheme),
	db: Session = Depends(get_db),
):
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="No se pudo validar el token de autenticación",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(
			token,
			settings.jwt_secret_key,
			algorithms=[settings.jwt_algorithm],
		)
		email: str | None = payload.get("sub")
		if email is None:
			raise credentials_exception
	except JWTError:
		raise credentials_exception

	usuario = usuarios_repo.get_usuario_por_email(db, email)
	if usuario is None or not usuario.is_active:
		raise credentials_exception

	return usuario


def get_current_admin(
	current_user=Depends(get_current_user),
):
	if not current_user.is_admin:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
	return current_user


def get_current_user_optional(
	token: str | None = Depends(oauth2_scheme_optional),
	db: Session = Depends(get_db),
):
	if token is None:
		return None

	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="No se pudo validar el token de autenticación",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		payload = jwt.decode(
			token,
			settings.jwt_secret_key,
			algorithms=[settings.jwt_algorithm],
		)
		email: str | None = payload.get("sub")
		if email is None:
			raise credentials_exception
	except JWTError:
		raise credentials_exception

	usuario = usuarios_repo.get_usuario_por_email(db, email)
	if usuario is None or not usuario.is_active:
		raise credentials_exception

	return usuario
