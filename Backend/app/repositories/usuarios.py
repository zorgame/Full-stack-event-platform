from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import UsuarioTickets, Usuarios


def get_usuario(db: Session, usuario_id: int) -> Usuarios | None:
	stmt: Select[tuple[Usuarios]] = (
		select(Usuarios)
		.where(Usuarios.id == usuario_id)
		.options(selectinload(Usuarios.tickets).selectinload(UsuarioTickets.categoria))
	)
	return db.execute(stmt).scalars().first()


def get_usuario_por_email(db: Session, email: str) -> Usuarios | None:
	stmt: Select[tuple[Usuarios]] = select(Usuarios).where(Usuarios.email == email)
	return db.execute(stmt).scalars().first()


def listar_usuarios(db: Session, *, skip: int = 0, limit: int = 50) -> Sequence[Usuarios]:
	stmt: Select[tuple[Usuarios]] = (
		select(Usuarios)
		.order_by(Usuarios.id.desc())
		.offset(skip)
		.limit(limit)
	)
	return db.execute(stmt).scalars().all()


def crear_usuario(db: Session, usuario: Usuarios) -> Usuarios:
	db.add(usuario)
	db.commit()
	db.refresh(usuario)
	return usuario


def actualizar_usuario(db: Session, usuario: Usuarios) -> Usuarios:
	db.add(usuario)
	db.commit()
	db.refresh(usuario)
	return usuario


def contar_admins_activos(db: Session) -> int:
	stmt: Select[tuple[int]] = select(func.count(Usuarios.id)).where(
		Usuarios.is_admin.is_(True),
		Usuarios.is_active.is_(True),
	)
	return int(db.execute(stmt).scalar_one())


def eliminar_usuario(db: Session, usuario: Usuarios) -> None:
	db.delete(usuario)
	db.commit()
