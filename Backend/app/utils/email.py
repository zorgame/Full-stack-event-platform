import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings


logger = logging.getLogger("tickets_api")


def send_html_email(*, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
	if not settings.smtp_is_configured:
		logger.info("SMTP no configurado o deshabilitado; se omite envio de correo")
		return False

	message = EmailMessage()
	message["Subject"] = subject
	message["From"] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
	message["To"] = to_email
	message.set_content(text_body)
	message.add_alternative(html_body, subtype="html")

	try:
		if settings.smtp_use_ssl:
			with smtplib.SMTP_SSL(
				host=settings.smtp_host,
				port=settings.smtp_port,
				timeout=settings.smtp_timeout_seconds,
			) as smtp:
				smtp.login(settings.smtp_username, settings.smtp_password)
				smtp.send_message(message)
			return True

		with smtplib.SMTP(
			host=settings.smtp_host,
			port=settings.smtp_port,
			timeout=settings.smtp_timeout_seconds,
		) as smtp:
			smtp.ehlo()
			if settings.smtp_use_tls:
				context = ssl.create_default_context()
				smtp.starttls(context=context)
				smtp.ehlo()
			smtp.login(settings.smtp_username, settings.smtp_password)
			smtp.send_message(message)
			return True
	except Exception as exc:
		logger.exception("No fue posible enviar correo a %s: %s", to_email, exc)
		return False
