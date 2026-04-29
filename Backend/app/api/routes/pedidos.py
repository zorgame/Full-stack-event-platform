from collections.abc import Sequence
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.api.dependencies.security import (
	get_current_admin,
	get_current_user,
	get_current_user_optional,
)
from app.controllers import pedidos as pedidos_controller
from app.schemas.metrics import PedidosMetricasResponse, RegistroVisitaPayload, RegistroVisitaResponse
from app.schemas.tickets import PedidoCreate, PedidoEstadoUpdate, PedidoResponse
from app.services.visitas_metricas import registrar_visita


router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("/", response_model=PedidoResponse, status_code=201)
async def crear_pedido(
	pedido_in: PedidoCreate,
	current_user=Depends(get_current_user_optional),
	db: Session = Depends(get_db),
):
	try:
		return pedidos_controller.crear_pedido_para_usuario(
			db,
			usuario_id=current_user.id if current_user is not None else None,
			pedido_in=pedido_in,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/mis", response_model=Sequence[PedidoResponse])
async def listar_mis_pedidos(
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	return pedidos_controller.listar_pedidos_de_usuario(db, usuario_id=current_user.id)


@router.get("/", response_model=Sequence[PedidoResponse])
async def listar_pedidos_admin(
	skip: int = 0,
	limit: int = 50,
	estado: str | None = None,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	return pedidos_controller.listar_pedidos(db, skip=skip, limit=limit, estado=estado)


@router.get("/metricas", response_model=PedidosMetricasResponse)
async def obtener_metricas_pedidos_admin(
	rango: str = Query(default="30d"),
	fecha_desde: datetime | None = Query(default=None),
	fecha_hasta: datetime | None = Query(default=None),
	group_by: str = Query(default="day"),
	estado: str | None = Query(default=None),
	pais: str | None = Query(default=None),
	producto_ids: str | None = Query(default=None),
	categoria_ids: str | None = Query(default=None),
	min_total: float | None = Query(default=None, ge=0),
	max_total: float | None = Query(default=None, ge=0),
	top_n: int = Query(default=8, ge=3, le=20),
	ventas_solo_aprobadas: bool = Query(default=True),
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	return pedidos_controller.obtener_metricas_pedidos(
		db,
		rango=rango,
		fecha_desde=fecha_desde,
		fecha_hasta=fecha_hasta,
		group_by=group_by,
		estado=estado,
		pais=pais,
		producto_ids=producto_ids,
		categoria_ids=categoria_ids,
		min_total=min_total,
		max_total=max_total,
		top_n=top_n,
		ventas_solo_aprobadas=ventas_solo_aprobadas,
	)


@router.post("/metricas/visitas/register", response_model=RegistroVisitaResponse, status_code=status.HTTP_202_ACCEPTED)
async def registrar_visita_publica(payload: RegistroVisitaPayload):
	accepted = registrar_visita(visitor_id=payload.visitor_id, path=payload.path)
	return RegistroVisitaResponse(accepted=accepted)


@router.get("/{pedido_id}", response_model=PedidoResponse)
async def get_pedido(
	pedido_id: int,
	current_user=Depends(get_current_user),
	db: Session = Depends(get_db),
):
	pedido = pedidos_controller.get_pedido(db, pedido_id=pedido_id)
	if pedido is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

	if not current_user.is_admin and pedido.usuario_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

	return pedido


@router.patch("/{pedido_id}/estado", response_model=PedidoResponse)
async def actualizar_estado_pedido(
	pedido_id: int,
	payload: PedidoEstadoUpdate,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	try:
		pedido = pedidos_controller.actualizar_estado_pedido(
			db,
			pedido_id=pedido_id,
			nuevo_estado=payload.estado,
			usuario_id_asignacion=payload.usuario_id,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	if pedido is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

	return pedido


@router.delete("/{pedido_id}", status_code=204)
async def eliminar_pedido(
	pedido_id: int,
	db: Session = Depends(get_db),
	admin=Depends(get_current_admin),
):
	_ = admin
	deleted = pedidos_controller.eliminar_pedido(db, pedido_id=pedido_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
	return None
