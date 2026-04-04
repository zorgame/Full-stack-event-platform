from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.api.dependencies.security import get_current_admin
from app.controllers import categorias as categorias_controller
from app.schemas.tickets import CategoriaCreate, CategoriaResponse, CategoriaUpdate


router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("/", response_model=Sequence[CategoriaResponse])
async def listar_categorias(
	db: Session = Depends(get_db),
	producto_id: int | None = None,
	only_active: bool = True,
):
	return categorias_controller.listar_categorias(
		db,
		producto_id=producto_id,
		only_active=only_active,
	)


@router.get("/{categoria_id}", response_model=CategoriaResponse)
async def get_categoria(categoria_id: int, db: Session = Depends(get_db)):
	categoria = categorias_controller.get_categoria(db, categoria_id)
	if categoria is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
	return categoria


@router.post("/", response_model=CategoriaResponse, status_code=201)
async def crear_categoria(
	categoria_in: CategoriaCreate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return categorias_controller.crear_categoria(db, categoria_in)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{categoria_id}", response_model=CategoriaResponse)
async def actualizar_categoria(
	categoria_id: int,
	categoria_in: CategoriaUpdate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	categoria = categorias_controller.actualizar_categoria(
		db,
		categoria_id=categoria_id,
		categoria_in=categoria_in,
	)
	if categoria is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
	return categoria


@router.delete("/{categoria_id}", status_code=204)
async def eliminar_categoria(
	categoria_id: int,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	deleted = categorias_controller.eliminar_categoria(db, categoria_id=categoria_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
	return None
