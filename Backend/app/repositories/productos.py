from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Productos


def get_producto(db: Session, producto_id: int) -> Productos | None:
	return db.get(Productos, producto_id)


def get_productos(
	db: Session,
	*,
	skip: int = 0,
	limit: int = 20,
	only_active: bool = True,
) -> Sequence[Productos]:
	stmt: Select[tuple[Productos]] = select(Productos)
	if only_active:
		stmt = stmt.where(Productos.is_active.is_(True))

	stmt = (
		stmt
		.options(selectinload(Productos.categorias))
		.order_by(Productos.id.desc())
		.offset(skip)
		.limit(limit)
	)

	return db.execute(stmt).scalars().all()


def get_producto_with_categorias(db: Session, producto_id: int) -> Productos | None:
	stmt: Select[tuple[Productos]] = (
		select(Productos)
		.where(Productos.id == producto_id)
		.options(selectinload(Productos.categorias))
	)
	return db.execute(stmt).scalars().first()


def contar_productos_por_imagen(db: Session, *, imagen: str) -> int:
	stmt: Select[tuple[int]] = select(func.count(Productos.id)).where(Productos.imagen == imagen)
	return int(db.execute(stmt).scalar_one())


def crear_producto(db: Session, producto: Productos) -> Productos:
	db.add(producto)
	db.commit()
	db.refresh(producto)
	return producto


def actualizar_producto(db: Session, producto: Productos) -> Productos:
	db.add(producto)
	db.commit()
	db.refresh(producto)
	return producto


def eliminar_producto(db: Session, producto: Productos) -> None:
	db.delete(producto)
	db.commit()
