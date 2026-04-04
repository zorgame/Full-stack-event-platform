from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.api.dependencies.security import get_current_admin, get_current_user
from app.controllers import usuarios as usuarios_controller
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


router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("/me/tickets/transferencia", response_model=UsuarioTicketTransferResponse)
async def transferir_mis_tickets(
	payload: UsuarioTicketTransferRequest,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user),
):
	return usuarios_controller.transferir_ticket_usuario(
		db,
		usuario_origen_id=current_user.id,
		payload=payload,
	)


@router.post("/", response_model=UsuarioResponse, status_code=201)
async def crear_usuario_cliente(
	usuario_in: UsuarioCreate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return usuarios_controller.crear_usuario_cliente(db, usuario_in)
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc


@router.get("/", response_model=Sequence[UsuarioListResponse])
async def listar_usuarios(
	skip: int = 0,
	limit: int = 50,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	return usuarios_controller.listar_usuarios(db, skip=skip, limit=limit)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
	usuario_id: int,
	payload: UsuarioUpdate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return usuarios_controller.actualizar_usuario(db, usuario_id=usuario_id, payload=payload)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{usuario_id}", status_code=204)
async def eliminar_usuario(
	usuario_id: int,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	deleted = usuarios_controller.eliminar_usuario(db, usuario_id=usuario_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
	return None


@router.get("/{usuario_id}/tickets", response_model=list[UsuarioTicketResponse])
async def listar_tickets_usuario(
	usuario_id: int,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return usuarios_controller.listar_tickets_usuario(db, usuario_id=usuario_id)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{usuario_id}/tickets", response_model=UsuarioTicketResponse, status_code=201)
async def asignar_ticket_usuario(
	usuario_id: int,
	payload: UsuarioTicketCreate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return usuarios_controller.asignar_ticket_usuario(db, usuario_id=usuario_id, payload=payload)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{usuario_id}/tickets/{usuario_ticket_id}", response_model=UsuarioTicketResponse)
async def actualizar_ticket_usuario(
	usuario_id: int,
	usuario_ticket_id: int,
	payload: UsuarioTicketUpdate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return usuarios_controller.actualizar_ticket_usuario(
			db,
			usuario_id=usuario_id,
			usuario_ticket_id=usuario_ticket_id,
			payload=payload,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{usuario_id}/tickets/{usuario_ticket_id}", status_code=204)
async def eliminar_ticket_usuario(
	usuario_id: int,
	usuario_ticket_id: int,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	deleted = usuarios_controller.eliminar_ticket_usuario(
		db,
		usuario_id=usuario_id,
		usuario_ticket_id=usuario_ticket_id,
	)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket de usuario no encontrado")
	return None
