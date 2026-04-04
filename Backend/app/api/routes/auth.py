from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.api.dependencies.security import get_current_user
from app.schemas import Token, UsuarioResponse
from app.services import usuarios as usuarios_service
from app.utils.security import crear_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
	form_data: OAuth2PasswordRequestForm = Depends(),
	db: Session = Depends(get_db),
):
	usuario = usuarios_service.autenticar_usuario(db, email=form_data.username, password=form_data.password)
	if usuario is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Credenciales incorrectas",
			headers={"WWW-Authenticate": "Bearer"},
		)

	token = crear_access_token(sub=usuario.email)
	return Token(access_token=token)


@router.get("/me", response_model=UsuarioResponse)
async def me(current_user=Depends(get_current_user)):
	return current_user
