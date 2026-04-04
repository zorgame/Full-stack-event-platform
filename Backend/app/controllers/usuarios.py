from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.schemas.usuarios import (
	UsuarioCreate,
	UsuarioListResponse,
	UsuarioResponse,
	UsuarioTicketCreate,
	UsuarioTicketTransferRequest,
	UsuarioTicketTransferResponse,
	UsuarioTicketResponse,
	UsuarioTicketUpdate,
	UsuarioUpdate,
)

from fastapi import HTTPException, status
import logging
from app.services import usuarios as usuarios_service

logger = logging.getLogger("tickets_api")


def crear_usuario_cliente(db: Session, usuario_in: UsuarioCreate) -> UsuarioResponse:
	try:
		return usuarios_service.crear_usuario(db, usuario_in)
	except ValueError as e:
		logger.warning(f"Error de negocio creando usuario: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado creando usuario: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def listar_usuarios(db: Session, *, skip: int = 0, limit: int = 50) -> Sequence[UsuarioListResponse]:
	try:
		return usuarios_service.listar_usuarios(db, skip=skip, limit=limit)
	except Exception as e:
		logger.exception(f"Error inesperado listando usuarios: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def listar_tickets_usuario(db: Session, *, usuario_id: int) -> list[UsuarioTicketResponse]:
	try:
		return usuarios_service.listar_tickets_usuario(db, usuario_id=usuario_id)
	except Exception as e:
		logger.exception(f"Error inesperado listando tickets de usuario: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def actualizar_usuario(
	db: Session,
	*,
	usuario_id: int,
	payload: UsuarioUpdate,
) -> UsuarioResponse:
	try:
		return usuarios_service.actualizar_usuario(db, usuario_id=usuario_id, payload=payload)
	except ValueError as e:
		logger.warning(f"Error de negocio actualizando usuario: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado actualizando usuario: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def asignar_ticket_usuario(
	db: Session,
	*,
	usuario_id: int,
	payload: UsuarioTicketCreate,
) -> UsuarioTicketResponse:
	return usuarios_service.asignar_ticket_usuario(db, usuario_id=usuario_id, payload=payload)


def actualizar_ticket_usuario(
	db: Session,
	*,
	usuario_id: int,
	usuario_ticket_id: int,
	payload: UsuarioTicketUpdate,
) -> UsuarioTicketResponse:
	return usuarios_service.actualizar_ticket_usuario(
		db,
		usuario_id=usuario_id,
		usuario_ticket_id=usuario_ticket_id,
		payload=payload,
	)


def eliminar_ticket_usuario(db: Session, *, usuario_id: int, usuario_ticket_id: int) -> bool:
	return usuarios_service.eliminar_ticket_usuario(
		db,
		usuario_id=usuario_id,
		usuario_ticket_id=usuario_ticket_id,
	)


def eliminar_usuario(db: Session, *, usuario_id: int) -> bool:
	try:
		return usuarios_service.eliminar_usuario(db, usuario_id=usuario_id)
	except ValueError as e:
		logger.warning(f"Error de negocio eliminando usuario: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado eliminando usuario: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def transferir_ticket_usuario(
	db: Session,
	*,
	usuario_origen_id: int,
	payload: UsuarioTicketTransferRequest,
) -> UsuarioTicketTransferResponse:
	try:
		return usuarios_service.transferir_ticket_usuario(
			db,
			usuario_origen_id=usuario_origen_id,
			payload=payload,
		)
	except ValueError as e:
		logger.warning(f"Error de negocio transfiriendo ticket de usuario: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado transfiriendo ticket de usuario: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")
