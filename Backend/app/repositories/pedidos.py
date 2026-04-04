from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import DetallePedido, Pedidos


def get_pedido(db: Session, pedido_id: int) -> Pedidos | None:
	stmt: Select[tuple[Pedidos]] = (
		select(Pedidos)
		.where(Pedidos.id == pedido_id)
		.options(selectinload(Pedidos.detalles).selectinload(DetallePedido.categoria))
	)
	return db.execute(stmt).scalars().first()


def get_pedido_por_referencia(db: Session, referencia: str) -> Pedidos | None:
	stmt: Select[tuple[Pedidos]] = select(Pedidos).where(Pedidos.referencia == referencia)
	return db.execute(stmt).scalars().first()


def listar_pedidos_por_usuario(
	db: Session,
	*,
	usuario_id: int,
) -> Sequence[Pedidos]:
	stmt: Select[tuple[Pedidos]] = (
		select(Pedidos)
		.where(Pedidos.usuario_id == usuario_id)
		.options(selectinload(Pedidos.detalles).selectinload(DetallePedido.categoria))
	)
	return db.execute(stmt).scalars().all()


def listar_pedidos(
	db: Session,
	*,
	skip: int = 0,
	limit: int = 50,
	estados: Sequence[str] | None = None,
) -> Sequence[Pedidos]:
	stmt: Select[tuple[Pedidos]] = select(Pedidos)
	if estados:
		stmt = stmt.where(Pedidos.estado.in_(tuple(estados)))

	stmt = (
		stmt
		.options(selectinload(Pedidos.detalles).selectinload(DetallePedido.categoria))
		.order_by(Pedidos.id.desc())
		.offset(skip)
		.limit(limit)
	)
	return db.execute(stmt).scalars().all()


def crear_pedido(db: Session, pedido: Pedidos) -> Pedidos:
	db.add(pedido)
	db.commit()
	db.refresh(pedido)
	return pedido


def actualizar_pedido(db: Session, pedido: Pedidos) -> Pedidos:
	db.add(pedido)
	db.commit()
	db.refresh(pedido)
	return pedido


def eliminar_pedido(db: Session, pedido: Pedidos) -> None:
	db.delete(pedido)
	db.commit()
