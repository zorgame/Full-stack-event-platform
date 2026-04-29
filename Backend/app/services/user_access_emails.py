from __future__ import annotations

from decimal import Decimal
from html import escape

from app.core.config import settings
from app.models import Pedidos
from app.utils.email import send_html_email


def _dinero(valor: Decimal | int | float | str | None) -> str:
    if valor is None:
        return "0.00"
    numero = Decimal(str(valor))
    return f"{numero:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _login_url() -> str:
    base = str(settings.frontend_public_url or "").strip().rstrip("/")
    if not base:
        return "/login"
    return f"{base}/login"


def enviar_correo_acceso_pago(
    *,
    pedido: Pedidos,
    email: str,
    password_temporal: str | None,
) -> None:
    correo = str(email or "").strip()
    if not correo:
        return

    nombre = escape(str(pedido.nombre_completo or "Cliente"))
    referencia = escape(str(pedido.referencia or "Sin referencia"))
    total = _dinero(pedido.total)
    login_url = escape(_login_url())

    es_nuevo_usuario = bool(password_temporal)
    subject = "Acceso a tu compra en EventTix"

    credenciales_html = ""
    credenciales_text = ""

    if es_nuevo_usuario:
        credenciales_html = (
            f"<p><strong>Correo:</strong> {escape(correo)}<br />"
            f"<strong>Contraseña temporal:</strong> {escape(password_temporal or '')}</p>"
        )
        credenciales_text = (
            f"Correo: {correo}\n"
            f"Contrasena temporal: {password_temporal or ''}\n"
        )
    else:
        credenciales_html = (
            f"<p><strong>Correo:</strong> {escape(correo)}<br />"
            "<strong>Contraseña:</strong> usa la que ya tienes registrada.</p>"
        )
        credenciales_text = (
            f"Correo: {correo}\n"
            "Contrasena: usa la que ya tienes registrada.\n"
        )

    html_body = f"""
    <!doctype html>
    <html lang=\"es\">
      <body style=\"font-family:Arial,Helvetica,sans-serif;background:#f6f8fb;margin:0;padding:24px;color:#1f2d42;\">
        <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e4eaf3;border-radius:12px;\">
          <tr>
            <td style=\"padding:22px 24px;border-bottom:1px solid #e4eaf3;\">
              <h1 style=\"margin:0;font-size:22px;\">Pago confirmado</h1>
              <p style=\"margin:8px 0 0 0;color:#4a5b78;\">Tu pedido fue procesado correctamente.</p>
            </td>
          </tr>
          <tr>
            <td style=\"padding:20px 24px;\">
              <p>Hola <strong>{nombre}</strong>,</p>
              <p>Resumen de compra:</p>
              <p><strong>Pedido:</strong> #{pedido.id}<br />
              <strong>Referencia:</strong> {referencia}<br />
              <strong>Total:</strong> {total} USD</p>
              <h2 style=\"font-size:16px;margin-top:20px;\">Credenciales de acceso</h2>
              {credenciales_html}
              <p>Ingresa desde: <a href=\"{login_url}\">{login_url}</a></p>
              <p style=\"margin-top:22px;color:#4a5b78;\">EventTix</p>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    text_body = (
        "Pago confirmado\n\n"
        f"Pedido: #{pedido.id}\n"
        f"Referencia: {pedido.referencia}\n"
        f"Total: {total} USD\n\n"
        "Credenciales de acceso\n"
        f"{credenciales_text}\n"
        f"Login: {_login_url()}\n"
    )

    send_html_email(
        to_email=correo,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )


def _nombre_publico(nombre: str | None, email: str | None) -> str:
        valor = str(nombre or "").strip()
        if valor:
                return valor
        return str(email or "Cliente").strip() or "Cliente"


def enviar_correo_transferencia_tickets(
        *,
        transferencia_id: str,
        email_origen: str,
        email_destino: str,
        nombre_origen: str | None,
        nombre_destino: str | None,
        categoria_nombre: str,
        cantidad: int,
        nota: str | None = None,
) -> None:
        correo_origen = str(email_origen or "").strip()
        correo_destino = str(email_destino or "").strip()
        if not correo_origen and not correo_destino:
                return

        id_transferencia = escape(str(transferencia_id or "Sin ID"))
        categoria = escape(str(categoria_nombre or "Categoria"))
        cantidad_str = str(int(cantidad or 0))
        login_url = escape(_login_url())

        nombre_origen_publico = escape(_nombre_publico(nombre_origen, correo_origen))
        nombre_destino_publico = escape(_nombre_publico(nombre_destino, correo_destino))
        nota_html = ""
        nota_text = ""
        if str(nota or "").strip():
                nota_html = f"<p><strong>Nota:</strong> {escape(str(nota).strip())}</p>"
                nota_text = f"Nota: {str(nota).strip()}\n"

        if correo_origen:
                html_origen = f"""
                <!doctype html>
                <html lang="es">
                    <body style="font-family:Arial,Helvetica,sans-serif;background:#f6f8fb;margin:0;padding:24px;color:#1f2d42;">
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e4eaf3;border-radius:12px;">
                            <tr>
                                <td style="padding:22px 24px;border-bottom:1px solid #e4eaf3;">
                                    <h1 style="margin:0;font-size:22px;">Transferencia de tickets procesada</h1>
                                    <p style="margin:8px 0 0 0;color:#4a5b78;">Se notifico el movimiento en tu cuenta EventTix.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:20px 24px;">
                                    <p>Hola <strong>{nombre_origen_publico}</strong>,</p>
                                    <p>Tu transferencia fue registrada correctamente.</p>
                                    <p><strong>ID:</strong> {id_transferencia}<br />
                                    <strong>Destinatario:</strong> {nombre_destino_publico} ({escape(correo_destino or 'No disponible')})<br />
                                    <strong>Categoria:</strong> {categoria}<br />
                                    <strong>Cantidad:</strong> {cantidad_str}</p>
                                    {nota_html}
                                    <p>Ingresa a tu panel para revisar el detalle: <a href="{login_url}">{login_url}</a></p>
                                    <p style="margin-top:22px;color:#4a5b78;">EventTix</p>
                                </td>
                            </tr>
                        </table>
                    </body>
                </html>
                """

                text_origen = (
                        "Transferencia de tickets procesada\n\n"
                        f"ID: {transferencia_id}\n"
                        f"Destinatario: {_nombre_publico(nombre_destino, correo_destino)} ({correo_destino or 'No disponible'})\n"
                        f"Categoria: {categoria_nombre}\n"
                        f"Cantidad: {cantidad_str}\n"
                        f"{nota_text}"
                        f"Panel: {_login_url()}\n"
                )

                send_html_email(
                        to_email=correo_origen,
                        subject="Transferencia de tickets registrada",
                        html_body=html_origen,
                        text_body=text_origen,
                )

        if correo_destino:
                html_destino = f"""
                <!doctype html>
                <html lang="es">
                    <body style="font-family:Arial,Helvetica,sans-serif;background:#f6f8fb;margin:0;padding:24px;color:#1f2d42;">
                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;margin:0 auto;background:#ffffff;border:1px solid #e4eaf3;border-radius:12px;">
                            <tr>
                                <td style="padding:22px 24px;border-bottom:1px solid #e4eaf3;">
                                    <h1 style="margin:0;font-size:22px;">Recibiste tickets en tu cuenta</h1>
                                    <p style="margin:8px 0 0 0;color:#4a5b78;">Se acredito una transferencia en tu perfil EventTix.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:20px 24px;">
                                    <p>Hola <strong>{nombre_destino_publico}</strong>,</p>
                                    <p>Se te asignaron tickets mediante transferencia interna.</p>
                                    <p><strong>ID:</strong> {id_transferencia}<br />
                                    <strong>Origen:</strong> {nombre_origen_publico} ({escape(correo_origen or 'No disponible')})<br />
                                    <strong>Categoria:</strong> {categoria}<br />
                                    <strong>Cantidad:</strong> {cantidad_str}</p>
                                    {nota_html}
                                    <p>Ingresa a tu panel para revisar el detalle: <a href="{login_url}">{login_url}</a></p>
                                    <p style="margin-top:22px;color:#4a5b78;">EventTix</p>
                                </td>
                            </tr>
                        </table>
                    </body>
                </html>
                """

                text_destino = (
                        "Recibiste tickets en tu cuenta\n\n"
                        f"ID: {transferencia_id}\n"
                        f"Origen: {_nombre_publico(nombre_origen, correo_origen)} ({correo_origen or 'No disponible'})\n"
                        f"Categoria: {categoria_nombre}\n"
                        f"Cantidad: {cantidad_str}\n"
                        f"{nota_text}"
                        f"Panel: {_login_url()}\n"
                )

                send_html_email(
                        to_email=correo_destino,
                        subject="Recibiste una transferencia de tickets",
                        html_body=html_destino,
                        text_body=text_destino,
                )
