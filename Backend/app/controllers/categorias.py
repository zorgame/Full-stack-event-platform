from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.schemas.tickets import CategoriaCreate, CategoriaResponse, CategoriaUpdate

from fastapi import HTTPException, status
import logging
from app.services import categorias as categorias_service

logger = logging.getLogger("tickets_api")


def listar_categorias(
    db: Session,
    *,
    producto_id: int | None = None,
    only_active: bool = True,
) -> Sequence[CategoriaResponse]:
    try:
        return categorias_service.listar_categorias(
            db,
            producto_id=producto_id,
            only_active=only_active,
        )
    except Exception as e:
        logger.exception(f"Error inesperado listando categorías: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


def get_categoria(db: Session, categoria_id: int) -> CategoriaResponse | None:
    try:
        result = categorias_service.get_categoria(db, categoria_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado obteniendo categoría: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


def crear_categoria(db: Session, categoria_in: CategoriaCreate) -> CategoriaResponse:
    try:
        return categorias_service.crear_categoria(db, categoria_in)
    except ValueError as e:
        logger.warning(f"Error de negocio creando categoría: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Error inesperado creando categoría: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


def actualizar_categoria(
    db: Session,
    *,
    categoria_id: int,
    categoria_in: CategoriaUpdate,
) -> CategoriaResponse | None:
    try:
        result = categorias_service.actualizar_categoria(
            db,
            categoria_id=categoria_id,
            categoria_in=categoria_in,
        )
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        return result
    except ValueError as e:
        logger.warning(f"Error de negocio actualizando categoría: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado actualizando categoría: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


def eliminar_categoria(db: Session, *, categoria_id: int) -> bool:
    try:
        result = categorias_service.eliminar_categoria(db, categoria_id=categoria_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado eliminando categoría: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
