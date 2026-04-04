from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.core import constants
from app.models import Categorias
from app.repositories import categorias as categorias_repo
from app.repositories import productos as productos_repo
from app.schemas.tickets import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from app.utils.cache import cache_delete, cache_delete_prefix, cache_get_json, cache_set_json


def _invalidate_productos_cache() -> None:
    cache_delete(constants.CACHE_KEY_PRODUCTOS_LIST)
    cache_delete_prefix(constants.CACHE_KEY_PRODUCTOS_LIST_PREFIX)


def _invalidate_categorias_cache() -> None:
    cache_delete_prefix(constants.CACHE_KEY_CATEGORIAS_LIST_PREFIX)


def _categorias_list_cache_key(*, producto_id: int | None, only_active: bool) -> str:
    return (
        f"{constants.CACHE_KEY_CATEGORIAS_LIST_PREFIX}"
        f"v1:{int(producto_id or 0)}:{1 if only_active else 0}"
    )


def listar_categorias(
    db: Session,
    *,
    producto_id: int | None = None,
    only_active: bool = True,
) -> Sequence[CategoriaResponse]:
    cache_key = _categorias_list_cache_key(producto_id=producto_id, only_active=only_active)
    cached = cache_get_json(cache_key)
    if cached is not None:
        return [CategoriaResponse.model_validate(c) for c in cached]

    categorias = categorias_repo.listar_categorias(
        db,
        producto_id=producto_id,
        only_active=only_active,
    )
    response = [CategoriaResponse.model_validate(c, from_attributes=True) for c in categorias]
    cache_set_json(
        cache_key,
        [item.model_dump(mode="json") for item in response],
        constants.CACHE_TTL_CATEGORIAS_SEGUNDOS,
    )
    return response


def get_categoria(db: Session, categoria_id: int) -> CategoriaResponse | None:
    categoria = categorias_repo.get_categoria(db, categoria_id)
    if categoria is None:
        return None
    return CategoriaResponse.model_validate(categoria, from_attributes=True)


def crear_categoria(db: Session, categoria_in: CategoriaCreate) -> CategoriaResponse:
    producto = productos_repo.get_producto(db, categoria_in.producto_id)
    if producto is None:
        raise ValueError("El producto indicado no existe")

    existing = categorias_repo.get_categoria_por_nombre(
        db,
        producto_id=categoria_in.producto_id,
        nombre=categoria_in.nombre,
    )
    if existing is not None:
        raise ValueError("Ya existe una categoría con ese nombre para el producto")

    categoria = Categorias(**categoria_in.model_dump())
    categoria = categorias_repo.crear_categoria(db, categoria)
    _invalidate_productos_cache()
    _invalidate_categorias_cache()
    return CategoriaResponse.model_validate(categoria, from_attributes=True)


def actualizar_categoria(
    db: Session,
    *,
    categoria_id: int,
    categoria_in: CategoriaUpdate,
) -> CategoriaResponse | None:
    categoria = categorias_repo.get_categoria(db, categoria_id)
    if categoria is None:
        return None

    data = categoria_in.model_dump(exclude_unset=True)
    for field_name, value in data.items():
        setattr(categoria, field_name, value)

    categoria = categorias_repo.actualizar_categoria(db, categoria)
    _invalidate_productos_cache()
    _invalidate_categorias_cache()
    return CategoriaResponse.model_validate(categoria, from_attributes=True)


def eliminar_categoria(db: Session, *, categoria_id: int) -> bool:
    categoria = categorias_repo.get_categoria(db, categoria_id)
    if categoria is None:
        return False

    categorias_repo.eliminar_categoria(db, categoria)
    _invalidate_productos_cache()
    _invalidate_categorias_cache()
    return True
