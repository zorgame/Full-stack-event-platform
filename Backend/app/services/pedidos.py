from collections.abc import Sequence
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import constants
from app.models import DetallePedido, Pedidos, UsuarioTickets
from app.repositories import categorias as categorias_repo
from app.repositories import pedidos as pedidos_repo
from app.repositories import usuario_tickets as usuario_tickets_repo
from app.repositories import usuarios as usuarios_repo
from app.services.pedido_emails import enviar_correo_evento_pedido
from app.schemas.tickets import DetallePedidoCreate, PedidoCreate, PedidoResponse, DetallePedidoResponse
def detalle_pedido_to_response(detalle: DetallePedido) -> DetallePedidoResponse:
	# Incluye el nombre del producto (evento) en la respuesta
	producto_nombre = None
	if detalle.categoria and detalle.categoria.producto:
		producto_nombre = detalle.categoria.producto.nombre
	return DetallePedidoResponse.model_validate(
		detalle,
		from_attributes=True,
		update={"producto_nombre": producto_nombre}
	)
from app.utils.cache import cache_delete, cache_delete_prefix, cache_get_json, cache_set_json


MAX_INTENTOS_REFERENCIA_PEDIDO = 5


def _invalidate_usuario_tickets_cache(usuario_id: int) -> None:
	key = f"{constants.CACHE_KEY_USUARIO_TICKETS_PREFIX}{usuario_id}"
	cache_delete(key)


def _invalidate_usuario_pedidos_cache(usuario_id: int) -> None:
	key = f"{constants.CACHE_KEY_PEDIDOS_USUARIO_PREFIX}{usuario_id}"
	cache_delete(key)


def _generate_referencia() -> str:
	return f"ORD-{uuid4().hex.upper()}"


def _es_colision_referencia(exc: IntegrityError) -> bool:
	mensaje = str(getattr(exc, "orig", exc)).lower()
	return "referencia" in mensaje


def _texto_limpio(valor: str | None) -> str | None:
	if valor is None:
		return None
	texto = str(valor).strip()
	return texto or None


def _build_detalles_snapshot(
	*, detalles_in: list[DetallePedidoCreate], db: Session
) -> tuple[list[DetallePedido], Decimal]:

	detalles: list[DetallePedido] = []
	total = Decimal("0")
	categoria_ids = {int(detalle.categoria_id) for detalle in detalles_in}
	categorias_por_id = {
		int(categoria.id): categoria
		for categoria in categorias_repo.listar_categorias_por_ids(
			db,
			categoria_ids=tuple(categoria_ids),
		)
	}

	for detalle_in in detalles_in:
		categoria = categorias_por_id.get(int(detalle_in.categoria_id))
		if categoria is None or not categoria.activo or not categoria.is_active:
			raise ValueError("Categoría no disponible")

		if detalle_in.cantidad <= 0:
			raise ValueError("Cantidad inválida")

		if (
			categoria.limite_por_usuario is not None
			and detalle_in.cantidad > categoria.limite_por_usuario
		):
			raise ValueError("Se supera el límite por usuario para esta categoría")

		if detalle_in.cantidad > categoria.unidades_disponibles:
			raise ValueError("No hay suficientes unidades disponibles")

		precio_unitario = Decimal(categoria.precio)
		subtotal = precio_unitario * detalle_in.cantidad

		detalle = DetallePedido(
			categoria=categoria,
			cantidad=detalle_in.cantidad,
			precio_unitario=precio_unitario,
			subtotal=subtotal,
		)
		detalles.append(detalle)
		total += subtotal

	return detalles, total


def _validar_usuario_asignacion(db: Session, *, usuario_id_asignacion: int | None) -> int | None:
	if usuario_id_asignacion is None:
		return None

	usuario = usuarios_repo.get_usuario(db, usuario_id_asignacion)
	if usuario is None:
		raise ValueError("El ID de usuario indicado no existe")
	if not usuario.is_active:
		raise ValueError("El usuario indicado está inactivo")

	return usuario.id


def _cantidad_por_categoria_en_pedido(pedido: Pedidos) -> dict[int, int]:
	cantidades: dict[int, int] = {}
	for detalle in pedido.detalles:
		categoria_id = int(detalle.categoria_id)
		cantidades[categoria_id] = cantidades.get(categoria_id, 0) + int(detalle.cantidad)
	return cantidades


def _ajustar_stock_pedido(*, pedido: Pedidos, db: Session, descontar: bool) -> None:
	for categoria_id, cantidad in _cantidad_por_categoria_en_pedido(pedido).items():
		categoria = categorias_repo.get_categoria_for_update(db, categoria_id)
		if categoria is None:
			raise ValueError("Categoría no disponible para actualizar stock")

		if descontar:
			if not categoria.activo or not categoria.is_active:
				raise ValueError("Categoría no disponible para confirmar el pedido")
			if cantidad > categoria.unidades_disponibles:
				raise ValueError("No hay suficientes unidades disponibles para confirmar el pedido")
			categoria.unidades_disponibles -= cantidad
		else:
			categoria.unidades_disponibles += cantidad

		db.add(categoria)


def _asignar_detalles_pedido_a_usuario(
	*,
	pedido: Pedidos,
	usuario_id: int,
	db: Session,
) -> None:
	for categoria_id, cantidad in _cantidad_por_categoria_en_pedido(pedido).items():
		existing = usuario_tickets_repo.get_usuario_ticket_by_categoria(
			db,
			usuario_id=usuario_id,
			categoria_id=categoria_id,
		)
		if existing is not None:
			existing.cantidad += cantidad
			db.add(existing)
			continue

		usuario_ticket = UsuarioTickets(
			usuario_id=usuario_id,
			categoria_id=categoria_id,
			cantidad=cantidad,
			nota=f"Asignado desde pedido {pedido.referencia}",
		)
		db.add(usuario_ticket)


def _desasignar_detalles_pedido_de_usuario(
	*,
	pedido: Pedidos,
	usuario_id: int,
	db: Session,
) -> None:
	cantidades = _cantidad_por_categoria_en_pedido(pedido)
	tickets_por_categoria: dict[int, UsuarioTickets | None] = {}

	for categoria_id, cantidad in cantidades.items():
		existing = usuario_tickets_repo.get_usuario_ticket_by_categoria(
			db,
			usuario_id=usuario_id,
			categoria_id=categoria_id,
		)
		tickets_por_categoria[categoria_id] = existing
		cantidad_actual = int(existing.cantidad) if existing is not None else 0
		if cantidad_actual < cantidad:
			raise ValueError(
				"No es posible revertir la asignación de tickets del pedido porque el usuario no tiene saldo suficiente"
			)

	for categoria_id, cantidad in cantidades.items():
		ticket = tickets_por_categoria[categoria_id]
		if ticket is None:
			continue

		ticket.cantidad = int(ticket.cantidad) - cantidad
		if ticket.cantidad <= 0:
			db.delete(ticket)
		else:
			db.add(ticket)


def crear_pedido(
	db: Session,
	*,
	usuario_id: int | None,
	pedido_in: PedidoCreate,
) -> PedidoResponse:
	if not pedido_in.detalles:
		raise ValueError("El pedido debe incluir al menos un detalle")

	if not bool(pedido_in.acepta_terminos):
		raise ValueError("Debes aceptar los términos y condiciones para continuar")

	pedido: Pedidos | None = None

	for intento in range(MAX_INTENTOS_REFERENCIA_PEDIDO):
		try:
			detalles, total = _build_detalles_snapshot(detalles_in=pedido_in.detalles, db=db)

			pedido = Pedidos(
				referencia=_generate_referencia(),
				estado=constants.PEDIDO_ESTADO_PENDIENTE,
				total=total,
				correo_electronico=_texto_limpio(pedido_in.correo_electronico),
				nombre_completo=_texto_limpio(pedido_in.nombre_completo),
				telefono=_texto_limpio(pedido_in.telefono),
				pais=_texto_limpio(pedido_in.pais),
				documento=_texto_limpio(pedido_in.documento),
				usuario_id=usuario_id,
			)
			pedido.detalles = detalles

			db.add(pedido)
			db.commit()
			db.refresh(pedido)
			break
		except IntegrityError as exc:
			db.rollback()
			es_colision_referencia = _es_colision_referencia(exc)
			if es_colision_referencia and intento < MAX_INTENTOS_REFERENCIA_PEDIDO - 1:
				continue
			if es_colision_referencia:
				raise ValueError(
					"No fue posible generar una referencia única para el pedido. Intenta de nuevo"
				) from exc
			raise ValueError("No fue posible crear el pedido. Verifica los datos") from exc
		except Exception:
			db.rollback()
			raise

	if pedido is None:
		raise ValueError("No fue posible generar una referencia única para el pedido. Intenta de nuevo")

	if usuario_id is not None:
		_invalidate_usuario_pedidos_cache(usuario_id)

	cache_delete_prefix(constants.CACHE_KEY_PEDIDOS_METRICAS_PREFIX)

	enviar_correo_evento_pedido(pedido=pedido, evento="creado")

	return PedidoResponse.model_validate(pedido, from_attributes=True)


def listar_pedidos_usuario(
	db: Session,
	*,
	usuario_id: int,
) -> Sequence[PedidoResponse]:
	cache_key = f"{constants.CACHE_KEY_PEDIDOS_USUARIO_PREFIX}{usuario_id}"
	cached = cache_get_json(cache_key)
	if cached is not None:
		return [PedidoResponse.model_validate(item) for item in cached]

	pedidos = pedidos_repo.listar_pedidos_por_usuario(db, usuario_id=usuario_id)

	result: list[PedidoResponse] = []
	for p in pedidos:
		detalles = [detalle_pedido_to_response(d) for d in p.detalles]
		pedido_dict = p.__dict__.copy()
		pedido_dict["detalles"] = detalles
		result.append(PedidoResponse.model_validate(pedido_dict, from_attributes=True))

	cache_set_json(
		cache_key,
		[item.model_dump(mode="json") for item in result],
		constants.CACHE_TTL_PEDIDOS_USUARIO_SEGUNDOS,
	)
	return result


def listar_pedidos(
	db: Session,
	*,
	skip: int = 0,
	limit: int = 50,
	estado: str | None = None,
) -> Sequence[PedidoResponse]:
	estados_filtrados: list[str] | None = None
	if estado is not None:
		candidatos = [str(valor).strip().lower() for valor in str(estado).split(",")]
		estados_filtrados = [valor for valor in candidatos if valor]
		if not estados_filtrados:
			estados_filtrados = None
		else:
			invalidos = [
				valor for valor in estados_filtrados if valor not in constants.PEDIDO_ESTADOS_VALIDOS
			]
			if invalidos:
				raise ValueError("Estado de pedido no válido")

	pedidos = pedidos_repo.listar_pedidos(
		db,
		skip=skip,
		limit=limit,
		estados=estados_filtrados,
	)
	result: list[PedidoResponse] = []
	for p in pedidos:
		detalles = [detalle_pedido_to_response(d) for d in p.detalles]
		pedido_dict = p.__dict__.copy()
		pedido_dict["detalles"] = detalles
		result.append(PedidoResponse.model_validate(pedido_dict, from_attributes=True))
	return result


def get_pedido(db: Session, *, pedido_id: int) -> PedidoResponse | None:
	pedido = pedidos_repo.get_pedido(db, pedido_id)
	if pedido is None:
		return None
	return PedidoResponse.model_validate(pedido, from_attributes=True)


def actualizar_estado_pedido(
	db: Session,
	*,
	pedido_id: int,
	nuevo_estado: str,
	usuario_id_asignacion: int | None = None,
) -> PedidoResponse | None:
	nuevo_estado = str(nuevo_estado or "").strip().lower()

	if nuevo_estado not in constants.PEDIDO_ESTADOS_VALIDOS:
		raise ValueError("Estado de pedido no válido")

	if nuevo_estado != constants.PEDIDO_ESTADO_PAGADO and usuario_id_asignacion is not None:
		raise ValueError("Solo puedes asignar usuario cuando el pedido se aprueba")

	pedido = pedidos_repo.get_pedido(db, pedido_id)
	if pedido is None:
		return None

	estado_anterior = pedido.estado
	usuario_anterior_id = pedido.usuario_id

	usuario_objetivo_id = _validar_usuario_asignacion(
		db,
		usuario_id_asignacion=usuario_id_asignacion,
	)

	usuarios_cache_invalidate: set[int] = set()

	if estado_anterior == constants.PEDIDO_ESTADO_PAGADO and nuevo_estado != constants.PEDIDO_ESTADO_PAGADO:
		_ajustar_stock_pedido(pedido=pedido, db=db, descontar=False)
		if usuario_anterior_id is not None:
			_desasignar_detalles_pedido_de_usuario(
				pedido=pedido,
				usuario_id=usuario_anterior_id,
				db=db,
			)
			usuarios_cache_invalidate.add(usuario_anterior_id)

	if estado_anterior != constants.PEDIDO_ESTADO_PAGADO and nuevo_estado == constants.PEDIDO_ESTADO_PAGADO:
		_ajustar_stock_pedido(pedido=pedido, db=db, descontar=True)

		usuario_final_id = usuario_objetivo_id if usuario_objetivo_id is not None else usuario_anterior_id
		if usuario_final_id is not None:
			_asignar_detalles_pedido_a_usuario(
				pedido=pedido,
				usuario_id=usuario_final_id,
				db=db,
			)
			usuarios_cache_invalidate.add(usuario_final_id)
		pedido.usuario_id = usuario_final_id

	if (
		estado_anterior == constants.PEDIDO_ESTADO_PAGADO
		and nuevo_estado == constants.PEDIDO_ESTADO_PAGADO
		and usuario_objetivo_id is not None
	):
		if usuario_anterior_id is None:
			_asignar_detalles_pedido_a_usuario(
				pedido=pedido,
				usuario_id=usuario_objetivo_id,
				db=db,
			)
			pedido.usuario_id = usuario_objetivo_id
			usuarios_cache_invalidate.add(usuario_objetivo_id)
		elif usuario_anterior_id != usuario_objetivo_id:
			_desasignar_detalles_pedido_de_usuario(
				pedido=pedido,
				usuario_id=usuario_anterior_id,
				db=db,
			)
			_asignar_detalles_pedido_a_usuario(
				pedido=pedido,
				usuario_id=usuario_objetivo_id,
				db=db,
			)
			pedido.usuario_id = usuario_objetivo_id
			usuarios_cache_invalidate.update({usuario_anterior_id, usuario_objetivo_id})

	pedido.estado = nuevo_estado
	db.add(pedido)
	try:
		db.commit()
	except IntegrityError as exc:
		db.rollback()
		raise ValueError("No fue posible actualizar el pedido sin duplicar asignaciones") from exc

	db.refresh(pedido)

	if pedido.usuario_id is not None:
		usuarios_cache_invalidate.add(pedido.usuario_id)

	for usuario_id in usuarios_cache_invalidate:
		_invalidate_usuario_tickets_cache(usuario_id)
		_invalidate_usuario_pedidos_cache(usuario_id)

	cache_delete_prefix(constants.CACHE_KEY_PEDIDOS_METRICAS_PREFIX)

	if estado_anterior != nuevo_estado:
		if nuevo_estado == constants.PEDIDO_ESTADO_PAGADO:
			enviar_correo_evento_pedido(pedido=pedido, evento="confirmado")
		elif nuevo_estado == constants.PEDIDO_ESTADO_CANCELADO:
			enviar_correo_evento_pedido(pedido=pedido, evento="cancelado")
		elif nuevo_estado == constants.PEDIDO_ESTADO_FALLIDO:
			enviar_correo_evento_pedido(pedido=pedido, evento="rechazado")

	return PedidoResponse.model_validate(pedido, from_attributes=True)


def eliminar_pedido(db: Session, *, pedido_id: int) -> bool:
	pedido = pedidos_repo.get_pedido(db, pedido_id)
	if pedido is None:
		return False

	usuario_id = pedido.usuario_id
	pedidos_repo.eliminar_pedido(db, pedido)

	if usuario_id is not None:
		_invalidate_usuario_tickets_cache(usuario_id)
		_invalidate_usuario_pedidos_cache(usuario_id)

	cache_delete_prefix(constants.CACHE_KEY_PEDIDOS_METRICAS_PREFIX)

	return True
