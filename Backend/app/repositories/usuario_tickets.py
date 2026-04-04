from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import UsuarioTickets


def get_usuario_ticket(db: Session, usuario_ticket_id: int) -> UsuarioTickets | None:
    stmt: Select[tuple[UsuarioTickets]] = (
        select(UsuarioTickets)
        .where(UsuarioTickets.id == usuario_ticket_id)
        .options(selectinload(UsuarioTickets.categoria))
    )
    return db.execute(stmt).scalars().first()


def get_usuario_ticket_by_categoria(
    db: Session,
    *,
    usuario_id: int,
    categoria_id: int,
) -> UsuarioTickets | None:
    stmt: Select[tuple[UsuarioTickets]] = (
        select(UsuarioTickets)
        .where(
            UsuarioTickets.usuario_id == usuario_id,
            UsuarioTickets.categoria_id == categoria_id,
        )
        .options(selectinload(UsuarioTickets.categoria))
    )
    return db.execute(stmt).scalars().first()


def listar_tickets_usuario(db: Session, *, usuario_id: int) -> Sequence[UsuarioTickets]:
    stmt: Select[tuple[UsuarioTickets]] = (
        select(UsuarioTickets)
        .where(UsuarioTickets.usuario_id == usuario_id)
        .options(selectinload(UsuarioTickets.categoria))
        .order_by(UsuarioTickets.id.desc())
    )
    return db.execute(stmt).scalars().all()


def crear_usuario_ticket(db: Session, usuario_ticket: UsuarioTickets) -> UsuarioTickets:
    db.add(usuario_ticket)
    db.commit()
    db.refresh(usuario_ticket)
    return usuario_ticket


def actualizar_usuario_ticket(db: Session, usuario_ticket: UsuarioTickets) -> UsuarioTickets:
    db.add(usuario_ticket)
    db.commit()
    db.refresh(usuario_ticket)
    return usuario_ticket


def eliminar_usuario_ticket(db: Session, usuario_ticket: UsuarioTickets) -> None:
    db.delete(usuario_ticket)
    db.commit()
