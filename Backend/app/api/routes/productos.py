from collections.abc import Sequence

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.api.dependencies.security import get_current_admin
from app.controllers import productos as productos_controller
from app.schemas.tickets import (
	CategoriaCreateEnProducto,
	CategoriaResponse,
	ProductoCreate,
	ProductoImagenUploadResponse,
	ProductoResponse,
	ProductoUpdate,
)


router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("/", response_model=Sequence[ProductoResponse])
async def listar_productos(
	skip: int = 0,
	limit: int = 20,
	only_active: bool = True,
	db: Session = Depends(get_db),
):
	return productos_controller.listar_productos(
		db,
		skip=skip,
		limit=limit,
		only_active=only_active,
	)


@router.post("/", response_model=ProductoResponse, status_code=201)
async def crear_producto(
	producto_in: ProductoCreate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	return productos_controller.crear_producto(db, producto_in)


@router.post("/upload-imagen", response_model=ProductoImagenUploadResponse, status_code=201)
async def subir_imagen_producto(
	file: UploadFile = File(...),
	admin=Depends(get_current_admin),
):
	_ = admin
	return await productos_controller.subir_imagen_producto(file)


@router.get("/{producto_id}", response_model=ProductoResponse)
async def get_producto(producto_id: int, db: Session = Depends(get_db)):
	producto = productos_controller.get_producto(db, producto_id)
	if producto is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
	return producto


@router.put("/{producto_id}", response_model=ProductoResponse)
async def actualizar_producto(
	producto_id: int,
	producto_in: ProductoUpdate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	producto = productos_controller.actualizar_producto(
		db,
		producto_id=producto_id,
		producto_in=producto_in,
	)
	if producto is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
	return producto


@router.delete("/{producto_id}", status_code=204)
async def eliminar_producto(
	producto_id: int,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	deleted = productos_controller.eliminar_producto(db, producto_id=producto_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
	return None


@router.post("/{producto_id}/categorias", response_model=CategoriaResponse, status_code=201)
async def crear_categoria_en_producto(
	producto_id: int,
	categoria_in: CategoriaCreateEnProducto,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		return productos_controller.crear_categoria_en_producto(
			db,
			producto_id=producto_id,
			categoria_in=categoria_in,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
