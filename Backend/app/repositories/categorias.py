from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Categorias


def get_categoria(db: Session, categoria_id: int) -> Categorias | None:
	return db.get(Categorias, categoria_id)


def get_categoria_for_update(db: Session, categoria_id: int) -> Categorias | None:
	stmt: Select[tuple[Categorias]] = (
		select(Categorias)
		.where(Categorias.id == categoria_id)
		.with_for_update()
	)
	return db.execute(stmt).scalars().first()


def get_categoria_por_nombre(db: Session, *, producto_id: int, nombre: str) -> Categorias | None:
	stmt: Select[tuple[Categorias]] = select(Categorias).where(
		Categorias.producto_id == producto_id,
		Categorias.nombre == nombre,
	)
	return db.execute(stmt).scalars().first()


def listar_categorias_por_ids(db: Session, *, categoria_ids: Sequence[int]) -> Sequence[Categorias]:
	if not categoria_ids:
		return []

	stmt: Select[tuple[Categorias]] = select(Categorias).where(Categorias.id.in_(tuple(categoria_ids)))
	return db.execute(stmt).scalars().all()


def listar_categorias(
	db: Session,
	*,
	producto_id: int | None = None,
	only_active: bool = True,
) -> Sequence[Categorias]:
	stmt: Select[tuple[Categorias]] = select(Categorias)
	if producto_id is not None:
		stmt = stmt.where(Categorias.producto_id == producto_id)
	if only_active:
		stmt = stmt.where(Categorias.is_active.is_(True))
	stmt = stmt.order_by(Categorias.nombre.asc())
	return db.execute(stmt).scalars().all()


def crear_categoria(db: Session, categoria: Categorias) -> Categorias:
	db.add(categoria)
	db.commit()
	db.refresh(categoria)
	return categoria


def actualizar_categoria(db: Session, categoria: Categorias) -> Categorias:
	db.add(categoria)
	db.commit()
	db.refresh(categoria)
	return categoria


def eliminar_categoria(db: Session, categoria: Categorias) -> None:
	db.delete(categoria)
	db.commit()
