from sqlalchemy.orm import Session
import logging
from datetime import datetime
from uuid import uuid4

from app.core import constants
from app.repositories import categorias as categorias_repo
from app.repositories import usuario_tickets as usuario_tickets_repo
from app.repositories import usuarios as usuarios_repo
from app.schemas.usuarios import (
	UsuarioTicketTransferRequest,
	UsuarioTicketTransferResponse,
	UsuarioTicketCreate,
	UsuarioTicketResponse,
	UsuarioTicketUpdate,
)
from app.schemas.usuarios import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.schemas.usuarios import UsuarioListResponse
from app.services.user_access_emails import enviar_correo_transferencia_tickets
from app.utils.cache import cache_delete_prefix, cache_get_json, cache_set_json
from app.utils.security import generar_hash_password, verificar_password


logger = logging.getLogger("tickets_api")


def _usuarios_list_cache_key(*, skip: int, limit: int) -> str:
	return f"{constants.CACHE_KEY_USUARIOS_LIST_PREFIX}v1:{int(skip)}:{int(limit)}"


def _usuario_tickets_cache_key(*, usuario_id: int) -> str:
	return f"{constants.CACHE_KEY_USUARIO_TICKETS_PREFIX}{int(usuario_id)}"


def _invalidate_usuarios_cache() -> None:
	cache_delete_prefix(constants.CACHE_KEY_USUARIOS_LIST_PREFIX)


def _invalidate_usuario_tickets_cache(*, usuario_id: int) -> None:
	cache_delete_prefix(_usuario_tickets_cache_key(usuario_id=usuario_id))


def _validar_no_ultimo_admin_activo(db: Session, *, usuario_actual, data_update: dict) -> None:
	if not usuario_actual.is_admin or not usuario_actual.is_active:
		return

	se_desactiva = data_update.get("is_active") is False
	se_quita_admin = data_update.get("is_admin") is False
	if not se_desactiva and not se_quita_admin:
		return

	admins_activos = usuarios_repo.contar_admins_activos(db)
	if admins_activos <= 1:
		raise ValueError("No puedes desactivar o degradar al ultimo administrador activo")


def crear_usuario(db: Session, usuario_in: UsuarioCreate, *, is_admin: bool = False) -> UsuarioResponse:
	existing = usuarios_repo.get_usuario_por_email(db, usuario_in.email)
	if existing is not None:
		raise ValueError("El email ya está registrado")

	from app.models import Usuarios

	usuario = Usuarios(
		email=usuario_in.email,
		telefono=usuario_in.telefono,
		nombre=usuario_in.nombre,
		apellido=usuario_in.apellido,
		pais=usuario_in.pais,
		hashed_password=generar_hash_password(usuario_in.password),
		is_admin=usuario_in.is_admin if usuario_in.is_admin is not None else is_admin,
	)

	usuario = usuarios_repo.crear_usuario(db, usuario)
	_invalidate_usuarios_cache()
	return UsuarioResponse.model_validate(usuario, from_attributes=True)


def autenticar_usuario(db: Session, email: str, password: str):
	from app.models import Usuarios

	usuario = usuarios_repo.get_usuario_por_email(db, email)
	if usuario is None:
		return None

	try:
		if not verificar_password(password, usuario.hashed_password):
			return None
	except Exception as exc:
		logger.warning("No se pudo verificar contraseña para %s: %s", email, exc)
		return None

	return usuario


def actualizar_usuario(db: Session, *, usuario_id: int, payload: UsuarioUpdate) -> UsuarioResponse:
	usuario = usuarios_repo.get_usuario(db, usuario_id)
	if usuario is None:
		raise ValueError("Usuario no encontrado")

	data = payload.model_dump(exclude_unset=True)
	_validar_no_ultimo_admin_activo(db, usuario_actual=usuario, data_update=data)

	new_password = data.pop("password", None)
	if new_password is not None:
		usuario.hashed_password = generar_hash_password(new_password)

	for field_name, value in data.items():
		setattr(usuario, field_name, value)

	usuario = usuarios_repo.actualizar_usuario(db, usuario)
	_invalidate_usuarios_cache()
	_invalidate_usuario_tickets_cache(usuario_id=usuario.id)
	return UsuarioResponse.model_validate(usuario, from_attributes=True)


def eliminar_usuario(db: Session, *, usuario_id: int) -> bool:
	usuario = usuarios_repo.get_usuario(db, usuario_id)
	if usuario is None:
		return False

	_validar_no_ultimo_admin_activo(db, usuario_actual=usuario, data_update={"is_active": False})
	usuarios_repo.eliminar_usuario(db, usuario)
	_invalidate_usuarios_cache()
	_invalidate_usuario_tickets_cache(usuario_id=usuario_id)
	return True


def listar_tickets_usuario(db: Session, *, usuario_id: int) -> list[UsuarioTicketResponse]:
	usuario = usuarios_repo.get_usuario(db, usuario_id)
	if usuario is None:
		raise ValueError("Usuario no encontrado")

	cache_key = _usuario_tickets_cache_key(usuario_id=usuario_id)
	cached = cache_get_json(cache_key)
	if cached is not None:
		return [UsuarioTicketResponse.model_validate(item) for item in cached]

	tickets = usuario_tickets_repo.listar_tickets_usuario(db, usuario_id=usuario_id)
	response = [UsuarioTicketResponse.model_validate(t, from_attributes=True) for t in tickets]
	cache_set_json(
		cache_key,
		[item.model_dump(mode="json") for item in response],
		constants.CACHE_TTL_TICKETS_USUARIO_SEGUNDOS,
	)
	return response


def listar_usuarios(db: Session, *, skip: int = 0, limit: int = 50) -> list[UsuarioListResponse]:
	cache_key = _usuarios_list_cache_key(skip=skip, limit=limit)
	cached = cache_get_json(cache_key)
	if cached is not None:
		return [UsuarioListResponse.model_validate(item) for item in cached]

	usuarios = usuarios_repo.listar_usuarios(db, skip=skip, limit=limit)
	response = [UsuarioListResponse.model_validate(u, from_attributes=True) for u in usuarios]

	cache_set_json(
		cache_key,
		[item.model_dump(mode="json") for item in response],
		constants.CACHE_TTL_USUARIOS_SEGUNDOS,
	)
	return response


def asignar_ticket_usuario(
	db: Session,
	*,
	usuario_id: int,
	payload: UsuarioTicketCreate,
) -> UsuarioTicketResponse:
	usuario = usuarios_repo.get_usuario(db, usuario_id)
	if usuario is None:
		raise ValueError("Usuario no encontrado")

	categoria = categorias_repo.get_categoria(db, payload.categoria_id)
	if categoria is None or not categoria.activo or not categoria.is_active:
		raise ValueError("Categoría no disponible")

	if payload.cantidad <= 0:
		raise ValueError("Cantidad inválida")

	existing = usuario_tickets_repo.get_usuario_ticket_by_categoria(
		db,
		usuario_id=usuario_id,
		categoria_id=payload.categoria_id,
	)
	if existing is not None:
		existing.cantidad += payload.cantidad
		if payload.nota is not None:
			existing.nota = payload.nota
		existing = usuario_tickets_repo.actualizar_usuario_ticket(db, existing)
		_invalidate_usuario_tickets_cache(usuario_id=usuario_id)
		return UsuarioTicketResponse.model_validate(existing, from_attributes=True)

	from app.models import UsuarioTickets

	usuario_ticket = UsuarioTickets(
		usuario_id=usuario_id,
		categoria_id=payload.categoria_id,
		cantidad=payload.cantidad,
		nota=payload.nota,
	)
	usuario_ticket = usuario_tickets_repo.crear_usuario_ticket(db, usuario_ticket)
	_invalidate_usuario_tickets_cache(usuario_id=usuario_id)
	return UsuarioTicketResponse.model_validate(usuario_ticket, from_attributes=True)


def actualizar_ticket_usuario(
	db: Session,
	*,
	usuario_id: int,
	usuario_ticket_id: int,
	payload: UsuarioTicketUpdate,
) -> UsuarioTicketResponse:
	usuario_ticket = usuario_tickets_repo.get_usuario_ticket(db, usuario_ticket_id)
	if usuario_ticket is None or usuario_ticket.usuario_id != usuario_id:
		raise ValueError("Ticket de usuario no encontrado")

	data = payload.model_dump(exclude_unset=True)
	if "cantidad" in data and data["cantidad"] is not None and data["cantidad"] <= 0:
		raise ValueError("Cantidad inválida")

	for field_name, value in data.items():
		setattr(usuario_ticket, field_name, value)

	usuario_ticket = usuario_tickets_repo.actualizar_usuario_ticket(db, usuario_ticket)
	_invalidate_usuario_tickets_cache(usuario_id=usuario_id)
	return UsuarioTicketResponse.model_validate(usuario_ticket, from_attributes=True)


def eliminar_ticket_usuario(
	db: Session,
	*,
	usuario_id: int,
	usuario_ticket_id: int,
) -> bool:
	usuario_ticket = usuario_tickets_repo.get_usuario_ticket(db, usuario_ticket_id)
	if usuario_ticket is None or usuario_ticket.usuario_id != usuario_id:
		return False

	usuario_tickets_repo.eliminar_usuario_ticket(db, usuario_ticket)
	_invalidate_usuario_tickets_cache(usuario_id=usuario_id)
	return True


def transferir_ticket_usuario(
	db: Session,
	*,
	usuario_origen_id: int,
	payload: UsuarioTicketTransferRequest,
) -> UsuarioTicketTransferResponse:
	if not payload.confirmacion_expresa:
		raise ValueError("Debes confirmar expresamente la transferencia para continuar")

	usuario_origen = usuarios_repo.get_usuario(db, usuario_origen_id)
	if usuario_origen is None or not usuario_origen.is_active:
		raise ValueError("Usuario origen no valido")

	try:
		password_valida = verificar_password(payload.password, usuario_origen.hashed_password)
	except Exception as exc:
		logger.warning("No se pudo verificar contrasena para transferencia usuario=%s: %s", usuario_origen_id, exc)
		raise ValueError("No se pudo validar la contrasena") from exc

	if not password_valida:
		raise ValueError("Contrasena incorrecta")

	destinatario_email = str(payload.destinatario_email).strip().lower()
	usuario_destino = usuarios_repo.get_usuario_por_email(db, destinatario_email)
	if usuario_destino is None or not usuario_destino.is_active:
		raise ValueError("La cuenta destinataria no existe o esta inactiva")

	if int(usuario_destino.id) == int(usuario_origen_id):
		raise ValueError("No puedes transferirte tickets a tu propia cuenta")

	ticket_origen = usuario_tickets_repo.get_usuario_ticket(db, payload.usuario_ticket_id)
	if ticket_origen is None or int(ticket_origen.usuario_id) != int(usuario_origen_id):
		raise ValueError("El ticket seleccionado no pertenece a tu cuenta")

	if int(payload.cantidad) > int(ticket_origen.cantidad):
		raise ValueError("La cantidad solicitada supera el saldo disponible de tickets")

	ticket_destino = usuario_tickets_repo.get_usuario_ticket_by_categoria(
		db,
		usuario_id=int(usuario_destino.id),
		categoria_id=int(ticket_origen.categoria_id),
	)

	try:
		if ticket_destino is None:
			from app.models import UsuarioTickets

			ticket_destino = UsuarioTickets(
				usuario_id=int(usuario_destino.id),
				categoria_id=int(ticket_origen.categoria_id),
				cantidad=int(payload.cantidad),
				nota=payload.nota or f"Transferido desde usuario {usuario_origen_id}",
			)
			db.add(ticket_destino)
			db.flush()
		else:
			ticket_destino.cantidad = int(ticket_destino.cantidad) + int(payload.cantidad)
			if payload.nota:
				ticket_destino.nota = payload.nota
			db.add(ticket_destino)

		ticket_origen.cantidad = int(ticket_origen.cantidad) - int(payload.cantidad)
		if payload.nota:
			ticket_origen.nota = payload.nota

		if int(ticket_origen.cantidad) <= 0:
			db.delete(ticket_origen)
		else:
			db.add(ticket_origen)

		db.commit()
		db.refresh(ticket_destino)
	except Exception:
		db.rollback()
		raise

	_invalidate_usuario_tickets_cache(usuario_id=int(usuario_origen_id))
	_invalidate_usuario_tickets_cache(usuario_id=int(usuario_destino.id))

	transferencia_id = f"TR-{uuid4().hex[:12].upper()}"
	categoria_nombre = (
		str(ticket_origen.categoria.nombre).strip()
		if ticket_origen.categoria is not None and ticket_origen.categoria.nombre
		else f"Categoria #{int(ticket_origen.categoria_id)}"
	)
	nombre_origen = f"{str(usuario_origen.nombre or '').strip()} {str(usuario_origen.apellido or '').strip()}".strip()
	nombre_destino = f"{str(usuario_destino.nombre or '').strip()} {str(usuario_destino.apellido or '').strip()}".strip()

	try:
		enviar_correo_transferencia_tickets(
			transferencia_id=transferencia_id,
			email_origen=str(usuario_origen.email or "").strip(),
			email_destino=str(usuario_destino.email or "").strip(),
			nombre_origen=nombre_origen,
			nombre_destino=nombre_destino,
			categoria_nombre=categoria_nombre,
			cantidad=int(payload.cantidad),
			nota=payload.nota,
		)
	except Exception as exc:
		logger.warning(
			"No se pudo enviar notificacion de transferencia %s (origen=%s destino=%s): %s",
			transferencia_id,
			usuario_origen_id,
			int(usuario_destino.id),
			exc,
		)

	return UsuarioTicketTransferResponse(
		transferencia_id=transferencia_id,
		usuario_origen_id=int(usuario_origen_id),
		usuario_destino_id=int(usuario_destino.id),
		usuario_ticket_origen_id=int(payload.usuario_ticket_id),
		usuario_ticket_destino_id=int(ticket_destino.id),
		categoria_id=int(ticket_destino.categoria_id),
		cantidad_transferida=int(payload.cantidad),
		destinatario_email=destinatario_email,
		estado="procesada",
		fecha=datetime.utcnow(),
		nota=payload.nota,
	)
