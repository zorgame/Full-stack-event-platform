from collections.abc import Sequence

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.schemas.tickets import (
	CategoriaCreateEnProducto,
	CategoriaResponse,
	ProductoCreate,
	ProductoImagenUploadResponse,
	ProductoResponse,
	ProductoUpdate,
)

from fastapi import HTTPException, status
import logging
from app.services import productos as productos_service

logger = logging.getLogger("tickets_api")


def crear_producto(db: Session, producto_in: ProductoCreate) -> ProductoResponse:
	try:
		return productos_service.crear_producto(db, producto_in)
	except ValueError as e:
		logger.warning(f"Error de negocio creando producto: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado creando producto: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


async def subir_imagen_producto(file: UploadFile) -> ProductoImagenUploadResponse:
	try:
		imagen_url = await productos_service.subir_imagen_producto(file)
		return ProductoImagenUploadResponse(imagen=imagen_url, url=imagen_url)
	except ValueError as e:
		logger.warning(f"Error de negocio subiendo imagen de producto: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado subiendo imagen de producto: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def listar_productos(
	db: Session,
	*,
	skip: int = 0,
	limit: int = 20,
	only_active: bool = True,
) -> Sequence[ProductoResponse]:
	try:
		return productos_service.listar_productos_con_categorias(
			db,
			skip=skip,
			limit=limit,
			only_active=only_active,
		)
	except Exception as e:
		logger.exception(f"Error inesperado listando productos: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def get_producto(db: Session, producto_id: int) -> ProductoResponse | None:
	try:
		result = productos_service.get_producto(db, producto_id)
		if result is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
		return result
	except HTTPException:
		raise
	except Exception as e:
		logger.exception(f"Error inesperado obteniendo producto: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def actualizar_producto(
	db: Session,
	*,
	producto_id: int,
	producto_in: ProductoUpdate,
) -> ProductoResponse | None:
	try:
		result = productos_service.actualizar_producto(db, producto_id=producto_id, producto_in=producto_in)
		if result is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
		return result
	except ValueError as e:
		logger.warning(f"Error de negocio actualizando producto: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except HTTPException:
		raise
	except Exception as e:
		logger.exception(f"Error inesperado actualizando producto: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def eliminar_producto(db: Session, *, producto_id: int) -> bool:
	try:
		result = productos_service.eliminar_producto(db, producto_id=producto_id)
		if not result:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
		return result
	except HTTPException:
		raise
	except Exception as e:
		logger.exception(f"Error inesperado eliminando producto: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def crear_categoria_en_producto(
	db: Session,
	*,
	producto_id: int,
	categoria_in: CategoriaCreateEnProducto,
) -> CategoriaResponse:
	categoria = productos_service.crear_categoria_en_producto(
		db,
		producto_id=producto_id,
		categoria_in=categoria_in,
	)
	return CategoriaResponse.model_validate(categoria, from_attributes=True)
