from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session

from app.schemas.tickets import PedidoCreate, PedidoResponse
from app.schemas.metrics import PedidosMetricasResponse

from fastapi import HTTPException, status
import logging
from app.services import pedidos as pedidos_service
from app.services import pedidos_metricas as pedidos_metricas_service

logger = logging.getLogger("tickets_api")


def crear_pedido_para_usuario(
	db: Session,
	*,
	usuario_id: int | None,
	pedido_in: PedidoCreate,
) -> PedidoResponse:
	try:
		return pedidos_service.crear_pedido(db, usuario_id=usuario_id, pedido_in=pedido_in)
	except ValueError as e:
		logger.warning(f"Error de negocio creando pedido: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado creando pedido: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def listar_pedidos_de_usuario(
	db: Session,
	*,
	usuario_id: int,
) -> Sequence[PedidoResponse]:
	try:
		return pedidos_service.listar_pedidos_usuario(db, usuario_id=usuario_id)
	except Exception as e:
		logger.exception(f"Error inesperado listando pedidos de usuario: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def listar_pedidos(
	db: Session,
	*,
	skip: int = 0,
	limit: int = 50,
	estado: str | None = None,
) -> Sequence[PedidoResponse]:
	try:
		return pedidos_service.listar_pedidos(db, skip=skip, limit=limit, estado=estado)
	except ValueError as e:
		logger.warning(f"Error de negocio listando pedidos: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado listando pedidos: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def get_pedido(db: Session, *, pedido_id: int) -> PedidoResponse | None:
	try:
		result = pedidos_service.get_pedido(db, pedido_id=pedido_id)
		if result is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
		return result
	except HTTPException:
		raise
	except Exception as e:
		logger.exception(f"Error inesperado obteniendo pedido: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def actualizar_estado_pedido(
	db: Session,
	*,
	pedido_id: int,
	nuevo_estado: str,
	usuario_id_asignacion: int | None = None,
) -> PedidoResponse | None:
	try:
		result = pedidos_service.actualizar_estado_pedido(
			db,
			pedido_id=pedido_id,
			nuevo_estado=nuevo_estado,
			usuario_id_asignacion=usuario_id_asignacion,
		)
		if result is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
		return result
	except ValueError as e:
		logger.warning(f"Error de negocio actualizando estado de pedido: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except HTTPException:
		raise
	except Exception as e:
		logger.exception(f"Error inesperado actualizando estado de pedido: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def obtener_metricas_pedidos(
	db: Session,
	*,
	rango: str = "30d",
	fecha_desde: datetime | None = None,
	fecha_hasta: datetime | None = None,
	group_by: str = "day",
	estado: str | None = None,
	pais: str | None = None,
	producto_ids: str | None = None,
	categoria_ids: str | None = None,
	min_total: float | None = None,
	max_total: float | None = None,
	top_n: int = 8,
	ventas_solo_aprobadas: bool = True,
) -> PedidosMetricasResponse:
	try:
		return pedidos_metricas_service.obtener_metricas_pedidos(
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
	except ValueError as e:
		logger.warning(f"Error de negocio obteniendo métricas de pedidos: {e}")
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
	except Exception as e:
		logger.exception(f"Error inesperado obteniendo métricas de pedidos: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")


def eliminar_pedido(db: Session, *, pedido_id: int) -> bool:
	try:
		result = pedidos_service.eliminar_pedido(db, pedido_id=pedido_id)
		if not result:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
		return result
	except HTTPException:
		raise
	except Exception as e:
		logger.exception(f"Error inesperado eliminando pedido: {e}")
		raise HTTPException(status_code=500, detail="Error interno del servidor")
