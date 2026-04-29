from collections.abc import Sequence

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import constants
from app.core.config import settings
from app.models import Categorias, Productos
from app.repositories import categorias as categorias_repo
from app.repositories import productos as productos_repo
from app.schemas.tickets import CategoriaCreate, CategoriaCreateEnProducto, ProductoCreate, ProductoResponse, ProductoUpdate
from app.utils.cache import cache_delete, cache_delete_prefix, cache_get_json, cache_set_json
from app.utils.media import delete_local_media_file, is_local_media_url, save_uploaded_producto_image


def _invalidate_productos_cache() -> None:
	cache_delete(constants.CACHE_KEY_PRODUCTOS_LIST)
	cache_delete_prefix(constants.CACHE_KEY_PRODUCTOS_LIST_PREFIX)
	cache_delete_prefix(constants.CACHE_KEY_CATEGORIAS_LIST_PREFIX)


def _productos_list_cache_key(*, skip: int, limit: int, only_active: bool) -> str:
	return (
		f"{constants.CACHE_KEY_PRODUCTOS_LIST_PREFIX}"
		f"v2:{int(skip)}:{int(limit)}:{1 if only_active else 0}"
	)


def _cleanup_unused_local_image(db: Session, imagen: str | None) -> None:
	if not imagen or not is_local_media_url(imagen):
		return

	if productos_repo.contar_productos_por_imagen(db, imagen=imagen) > 0:
		return

	delete_local_media_file(imagen)


async def subir_imagen_producto(file: UploadFile) -> str:
	return await save_uploaded_producto_image(file)


def listar_productos_con_categorias(
	db: Session,
	*,
	skip: int = 0,
	limit: int = 20,
	only_active: bool = True,
) -> Sequence[ProductoResponse]:
	usa_cache_global = skip == 0 and limit == 20 and only_active
	cache_key = _productos_list_cache_key(skip=skip, limit=limit, only_active=only_active)
	cached = cache_get_json(cache_key)
	if cached is None and usa_cache_global:
		cached = cache_get_json(constants.CACHE_KEY_PRODUCTOS_LIST)
	if cached is not None:
		return [ProductoResponse.model_validate(item) for item in cached]

	productos = productos_repo.get_productos(
		db,
		skip=skip,
		limit=limit,
		only_active=only_active,
	)
	result: list[ProductoResponse] = [
		ProductoResponse.model_validate(p, from_attributes=True) for p in productos
	]

	payload = [item.model_dump(mode="json") for item in result]
	cache_set_json(
		cache_key,
		payload,
		constants.CACHE_TTL_PRODUCTOS_SEGUNDOS,
	)

	if usa_cache_global:
		cache_set_json(
			constants.CACHE_KEY_PRODUCTOS_LIST,
			payload,
			constants.CACHE_TTL_PRODUCTOS_SEGUNDOS,
		)
	return result


def crear_producto(db: Session, producto_in: ProductoCreate) -> ProductoResponse:
	if producto_in.categorias:
		nombres = [c.nombre.strip().lower() for c in producto_in.categorias]
		if len(nombres) != len(set(nombres)):
			raise ValueError("No puedes repetir nombres de categoría en el mismo producto")

	producto = Productos(
		nombre=producto_in.nombre,
		fecha=producto_in.fecha,
		ubicacion=producto_in.ubicacion,
		estadio=producto_in.estadio,
		ubicacion_estadio=producto_in.ubicacion_estadio,
		descripcion=producto_in.descripcion,
		imagen=producto_in.imagen,
		is_active=producto_in.is_active,
	)

	if producto_in.categorias:
		producto.categorias = [
			Categorias(
				nombre=categoria_in.nombre,
				descripcion=categoria_in.descripcion,
				precio=categoria_in.precio,
				moneda=categoria_in.moneda,
				unidades_disponibles=categoria_in.unidades_disponibles,
				limite_por_usuario=categoria_in.limite_por_usuario,
				activo=categoria_in.activo,
				is_active=categoria_in.is_active,
			)
			for categoria_in in producto_in.categorias
		]
		for categoria in producto.categorias:
			categoria.producto = producto

	producto = productos_repo.crear_producto(db, producto)

	_invalidate_productos_cache()

	return ProductoResponse.model_validate(producto, from_attributes=True)


def get_producto(db: Session, producto_id: int) -> ProductoResponse | None:
	producto = productos_repo.get_producto_with_categorias(db, producto_id)
	if producto is None:
		return None
	return ProductoResponse.model_validate(producto, from_attributes=True)


def actualizar_producto(db: Session, *, producto_id: int, producto_in: ProductoUpdate) -> ProductoResponse | None:
	producto = productos_repo.get_producto(db, producto_id)
	if producto is None:
		return None

	imagen_anterior = str(producto.imagen or "").strip() or None
	data = producto_in.model_dump(exclude_unset=True)
	for field_name, value in data.items():
		setattr(producto, field_name, value)

	producto = productos_repo.actualizar_producto(db, producto)
	_invalidate_productos_cache()

	if "imagen" in data and data.get("imagen") != imagen_anterior:
		_cleanup_unused_local_image(db, imagen_anterior)

	return ProductoResponse.model_validate(producto, from_attributes=True)


def eliminar_producto(db: Session, *, producto_id: int) -> bool:
	producto = productos_repo.get_producto(db, producto_id)
	if producto is None:
		return False

	imagen_eliminada = str(producto.imagen or "").strip() or None
	try:
		productos_repo.eliminar_producto(db, producto)
		_invalidate_productos_cache()
		_cleanup_unused_local_image(db, imagen_eliminada)
		return True
	except IntegrityError:
		# Si el producto tiene categorias referenciadas en pedidos/tickets, no se puede
		# eliminar fisicamente: se archiva para mantener la integridad historica.
		db.rollback()
		producto = productos_repo.get_producto_with_categorias(db, producto_id)
		if producto is None:
			return False

		producto.is_active = False
		for categoria in producto.categorias:
			categoria.activo = False
			categoria.is_active = False
			categoria.unidades_disponibles = 0
			categoria.limite_por_usuario = None

		productos_repo.actualizar_producto(db, producto)
		_invalidate_productos_cache()
		return True


def crear_categoria_en_producto(
	db: Session,
	*,
	categoria_in: CategoriaCreateEnProducto,
	producto_id: int,
) -> Categorias:
	producto = productos_repo.get_producto(db, producto_id)
	if producto is None:
		raise ValueError("El producto no existe")

	existing = categorias_repo.get_categoria_por_nombre(
		db,
		producto_id=producto_id,
		nombre=categoria_in.nombre,
	)
	if existing is not None:
		raise ValueError("Ya existe una categoría con ese nombre para el producto")

	categoria = Categorias(
		producto_id=producto_id,
		nombre=categoria_in.nombre,
		descripcion=categoria_in.descripcion,
		precio=categoria_in.precio,
		moneda=categoria_in.moneda,
		unidades_disponibles=categoria_in.unidades_disponibles,
		limite_por_usuario=categoria_in.limite_por_usuario,
		activo=categoria_in.activo,
		is_active=categoria_in.is_active,
	)

	categoria = categorias_repo.crear_categoria(db, categoria)
	_invalidate_productos_cache()
	return categoria
