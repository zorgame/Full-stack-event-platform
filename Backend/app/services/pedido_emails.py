from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from html import escape
from typing import Literal

from app.core import constants
from app.models import Pedidos
from app.utils.email import send_html_email


PedidoEmailEvento = Literal["creado", "confirmado", "rechazado", "cancelado"]


@dataclass(frozen=True)
class _PedidoEmailMeta:
	subject: str
	heading: str
	subheading: str
	status_label: str
	status_color: str


_EVENTOS_EMAIL: dict[PedidoEmailEvento, _PedidoEmailMeta] = {
	"creado": _PedidoEmailMeta(
		subject="Recibimos tu pedido en EventTix",
		heading="Tu pedido fue creado correctamente",
		subheading="Estamos revisando tu solicitud. Te notificaremos cuando cambie de estado.",
		status_label="Pendiente",
		status_color="#9a6a0a",
	),
	"confirmado": _PedidoEmailMeta(
		subject="Tu pedido fue confirmado",
		heading="Pago confirmado y pedido aprobado",
		subheading="Tu pedido ha sido validado por nuestro equipo.",
		status_label="Confirmado",
		status_color="#0f7a44",
	),
	"rechazado": _PedidoEmailMeta(
		subject="Actualizacion de tu pedido",
		heading="Tu pedido fue rechazado",
		subheading="No fue posible aprobar el pedido. Si deseas, puedes responder este correo para recibir asistencia.",
		status_label="Rechazado",
		status_color="#9d1f1f",
	),
	"cancelado": _PedidoEmailMeta(
		subject="Tu pedido fue cancelado",
		heading="Tu pedido fue cancelado",
		subheading="Tu pedido fue cancelado y ya no esta en proceso de pago. Si necesitas ayuda, responde este correo.",
		status_label="Cancelado",
		status_color="#8c2f00",
	),
}


def _estado_legible(estado: str) -> str:
	valor = str(estado or "").strip().lower()
	if valor == constants.PEDIDO_ESTADO_PENDIENTE:
		return "Pendiente"
	if valor == constants.PEDIDO_ESTADO_PAGADO:
		return "Confirmado"
	if valor == constants.PEDIDO_ESTADO_CANCELADO:
		return "Cancelado"
	if valor == constants.PEDIDO_ESTADO_FALLIDO:
		return "Rechazado"
	return valor or "Sin estado"


def _dinero(valor: Decimal | int | float | str | None) -> str:
	if valor is None:
		return "0.00"
	numero = Decimal(str(valor))
	return f"{numero:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _detalle_rows_html(pedido: Pedidos) -> str:
	rows: list[str] = []
	for detalle in pedido.detalles:
		nombre_categoria = (
			detalle.categoria.nombre if detalle.categoria is not None and detalle.categoria.nombre else f"Categoria #{detalle.categoria_id}"
		)
		rows.append(
			"""
			<tr>
			  <td style="padding:10px 8px;border-bottom:1px solid #e9edf3;color:#223047;">{categoria}</td>
			  <td style="padding:10px 8px;border-bottom:1px solid #e9edf3;color:#223047;text-align:center;">{cantidad}</td>
			  <td style="padding:10px 8px;border-bottom:1px solid #e9edf3;color:#223047;text-align:right;">{unitario} USD</td>
			  <td style="padding:10px 8px;border-bottom:1px solid #e9edf3;color:#223047;text-align:right;">{subtotal} USD</td>
			</tr>
			""".format(
				categoria=escape(str(nombre_categoria)),
				cantidad=int(detalle.cantidad),
				unitario=_dinero(detalle.precio_unitario),
				subtotal=_dinero(detalle.subtotal),
			)
		)

	if rows:
		return "".join(rows)

	return (
		'<tr><td colspan="4" style="padding:12px 8px;color:#6d7789;text-align:center;">'
		"No hay detalles disponibles para este pedido."
		"</td></tr>"
	)


def _build_html_email(pedido: Pedidos, meta: _PedidoEmailMeta) -> str:
	nombre = escape(str(pedido.nombre_completo or "Cliente"))
	referencia = escape(str(pedido.referencia or "Sin referencia"))
	estado = escape(_estado_legible(pedido.estado))
	correo = escape(str(pedido.correo_electronico or "No disponible"))
	telefono = escape(str(pedido.telefono or "No disponible"))
	documento = escape(str(pedido.documento or "No disponible"))
	pais = escape(str(pedido.pais or "No disponible"))
	fecha = pedido.fecha_creacion.strftime("%Y-%m-%d %H:%M") if pedido.fecha_creacion else "No disponible"
	total = _dinero(pedido.total)
	detalles_rows = _detalle_rows_html(pedido)

	return f"""
	<!doctype html>
	<html lang="es">
	  <body style="margin:0;padding:0;background:#f3f6fb;font-family:Arial,Helvetica,sans-serif;color:#1d2a3d;">
	    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:24px 12px;">
	      <tr>
	        <td align="center">
	          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:760px;background:#ffffff;border:1px solid #e3e8f2;border-radius:12px;overflow:hidden;">
	            <tr>
	              <td style="padding:22px 24px;background:linear-gradient(120deg,#0f5fd8 0%,#0dc7ff 100%);color:#ffffff;">
	                <p style="margin:0 0 6px 0;font-size:12px;letter-spacing:.08em;text-transform:uppercase;opacity:.9;">EventTix</p>
	                <h1 style="margin:0;font-size:24px;line-height:1.2;">{escape(meta.heading)}</h1>
	                <p style="margin:10px 0 0 0;font-size:14px;opacity:.92;">{escape(meta.subheading)}</p>
	              </td>
	            </tr>
	            <tr>
	              <td style="padding:22px 24px 14px 24px;">
	                <p style="margin:0 0 10px 0;font-size:14px;">Hola <strong>{nombre}</strong>,</p>
	                <p style="margin:0;font-size:14px;color:#42506a;">Resumen del pedido:</p>
	              </td>
	            </tr>
	            <tr>
	              <td style="padding:0 24px 14px 24px;">
	                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e5eaf4;border-radius:10px;background:#f9fbff;">
	                  <tr>
	                    <td style="padding:12px 14px;font-size:13px;color:#4e5f7f;">ID</td>
	                    <td style="padding:12px 14px;font-size:13px;font-weight:700;text-align:right;">#{pedido.id}</td>
	                  </tr>
	                  <tr>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:13px;color:#4e5f7f;">Referencia</td>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:13px;font-weight:700;text-align:right;">{referencia}</td>
	                  </tr>
	                  <tr>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:13px;color:#4e5f7f;">Estado</td>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;text-align:right;">
	                      <span style="display:inline-block;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:700;background:rgba(0,0,0,.05);color:{meta.status_color};">{escape(meta.status_label)} · {estado}</span>
	                    </td>
	                  </tr>
	                  <tr>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:13px;color:#4e5f7f;">Fecha</td>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:13px;text-align:right;">{escape(fecha)}</td>
	                  </tr>
	                  <tr>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:13px;color:#4e5f7f;">Total</td>
	                    <td style="padding:12px 14px;border-top:1px solid #e5eaf4;font-size:14px;font-weight:700;text-align:right;">{total} USD</td>
	                  </tr>
	                </table>
	              </td>
	            </tr>
	            <tr>
	              <td style="padding:0 24px 14px 24px;">
	                <h2 style="margin:0 0 8px 0;font-size:15px;color:#24324a;">Detalle de tickets</h2>
	                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e9edf3;border-radius:10px;background:#fff;overflow:hidden;">
	                  <thead>
	                    <tr style="background:#f5f8fd;">
	                      <th style="padding:10px 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#596b88;text-align:left;">Categoria</th>
	                      <th style="padding:10px 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#596b88;text-align:center;">Cant.</th>
	                      <th style="padding:10px 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#596b88;text-align:right;">Unitario</th>
	                      <th style="padding:10px 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#596b88;text-align:right;">Subtotal</th>
	                    </tr>
	                  </thead>
	                  <tbody>
	                    {detalles_rows}
	                  </tbody>
	                </table>
	              </td>
	            </tr>
	            <tr>
	              <td style="padding:0 24px 22px 24px;">
	                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e5eaf4;border-radius:10px;background:#fbfdff;">
	                  <tr>
	                    <td style="padding:10px 14px;font-size:12px;color:#5b6d8a;">Correo</td>
	                    <td style="padding:10px 14px;font-size:12px;color:#1f2f48;text-align:right;">{correo}</td>
	                  </tr>
	                  <tr>
	                    <td style="padding:10px 14px;border-top:1px solid #e5eaf4;font-size:12px;color:#5b6d8a;">Telefono</td>
	                    <td style="padding:10px 14px;border-top:1px solid #e5eaf4;font-size:12px;color:#1f2f48;text-align:right;">{telefono}</td>
	                  </tr>
	                  <tr>
	                    <td style="padding:10px 14px;border-top:1px solid #e5eaf4;font-size:12px;color:#5b6d8a;">Documento</td>
	                    <td style="padding:10px 14px;border-top:1px solid #e5eaf4;font-size:12px;color:#1f2f48;text-align:right;">{documento}</td>
	                  </tr>
	                  <tr>
	                    <td style="padding:10px 14px;border-top:1px solid #e5eaf4;font-size:12px;color:#5b6d8a;">Pais</td>
	                    <td style="padding:10px 14px;border-top:1px solid #e5eaf4;font-size:12px;color:#1f2f48;text-align:right;">{pais}</td>
	                  </tr>
	                </table>
	              </td>
	            </tr>
	            <tr>
	              <td style="padding:16px 24px;background:#f7f9fc;font-size:12px;color:#60708c;">
	                Este correo fue generado automaticamente por EventTix. Si tienes dudas, responde este mensaje.
	              </td>
	            </tr>
	          </table>
	        </td>
	      </tr>
	    </table>
	  </body>
	</html>
	"""


def _build_text_email(pedido: Pedidos, meta: _PedidoEmailMeta) -> str:
	lineas = [
		f"{meta.heading}",
		meta.subheading,
		"",
		f"ID: #{pedido.id}",
		f"Referencia: {pedido.referencia}",
		f"Estado: {_estado_legible(pedido.estado)}",
		f"Total: {_dinero(pedido.total)} USD",
		"",
		"Detalle:",
	]

	for detalle in pedido.detalles:
		nombre_categoria = (
			detalle.categoria.nombre if detalle.categoria is not None and detalle.categoria.nombre else f"Categoria #{detalle.categoria_id}"
		)
		lineas.append(
			f"- {nombre_categoria}: {int(detalle.cantidad)} x {_dinero(detalle.precio_unitario)} USD = {_dinero(detalle.subtotal)} USD"
		)

	lineas.extend([
		"",
		"EventTix",
	])
	return "\n".join(lineas)


def enviar_correo_evento_pedido(*, pedido: Pedidos, evento: PedidoEmailEvento) -> None:
	correo = str(pedido.correo_electronico or "").strip()
	if not correo:
		return

	meta = _EVENTOS_EMAIL.get(evento)
	if meta is None:
		return

	html_body = _build_html_email(pedido, meta)
	text_body = _build_text_email(pedido, meta)
	send_html_email(
		to_email=correo,
		subject=meta.subject,
		html_body=html_body,
		text_body=text_body,
	)
