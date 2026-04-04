from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from app.core.config import settings

USDC_PRODUCTION = "solana:EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class CrossmintApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details


@dataclass(frozen=True)
class OnrampConfig:
    env: str
    server_key: str
    client_key: str
    orders_base_url: str
    users_base_url: str
    recipient_wallet_address: str
    recipient_user_email: str
    recipient_chain: str
    token_locator: str
    payment_method: str
    support_whatsapp: str



def _safe_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}



def _normalize_env(value: str) -> str:
    normalized = str(value or "production").strip().lower()
    return normalized or "production"



def _host_for_env(env_name: str) -> str:
    _ = env_name
    return str(settings.crossmint_host or "").strip().rstrip("/")



def _normalize_support_whatsapp(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())



def _format_amount(amount: Decimal | str | float | int) -> str:
    if isinstance(amount, Decimal):
        decimal_value = amount
    else:
        try:
            decimal_value = Decimal(str(amount))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Monto de pago inválido") from exc

    if decimal_value <= 0:
        raise ValueError("El monto del pago debe ser mayor a cero")

    return f"{decimal_value.quantize(Decimal('0.01'))}"



def get_onramp_config(*, strict: bool = True) -> OnrampConfig:
    env_name = _normalize_env(settings.crossmint_env)
    host = _host_for_env(env_name)

    orders_base_url = (
        str(settings.crossmint_orders_base_url or "").strip().rstrip("/")
        or (f"{host}/api/2022-06-09" if host else "")
    )
    users_base_url = (
        str(settings.crossmint_users_base_url or "").strip().rstrip("/")
        or (f"{host}/api/2025-06-09" if host else "")
    )

    token_locator = str(settings.crossmint_token_locator or "").strip()
    if not token_locator:
        token_locator = USDC_PRODUCTION

    cfg = OnrampConfig(
        env=env_name,
        server_key=str(settings.crossmint_server_side_api_key or "").strip(),
        client_key=str(settings.crossmint_client_side_api_key or "").strip(),
        orders_base_url=orders_base_url,
        users_base_url=users_base_url,
        recipient_wallet_address=str(settings.crossmint_recipient_wallet_address or "").strip(),
        recipient_user_email=str(settings.crossmint_recipient_user_email or "").strip(),
        recipient_chain=str(settings.crossmint_recipient_chain or "solana").strip() or "solana",
        token_locator=token_locator,
        payment_method=str(settings.crossmint_payment_method or "checkoutcom-flow").strip() or "checkoutcom-flow",
        support_whatsapp=_normalize_support_whatsapp(settings.crossmint_support_whatsapp),
    )

    if strict:
        if cfg.env != "production":
            raise ValueError("CROSSMINT_ENV debe ser 'production' para esta integracion")

        missing: list[str] = []
        if not cfg.server_key:
            missing.append("CROSSMINT_SERVER_SIDE_API_KEY")
        if not cfg.orders_base_url:
            missing.append("CROSSMINT_ORDERS_BASE_URL")
        if not cfg.users_base_url:
            missing.append("CROSSMINT_USERS_BASE_URL")
        if not cfg.recipient_user_email:
            missing.append("CROSSMINT_RECIPIENT_USER_EMAIL")
        if not cfg.recipient_wallet_address:
            missing.append("CROSSMINT_RECIPIENT_WALLET_ADDRESS")

        if missing:
            raise ValueError("Faltan variables de entorno de pagos: " + ", ".join(missing))

    return cfg



def call_crossmint(
    *,
    method: str,
    url: str,
    server_key: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": server_key,
    }

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload,
            timeout=45,
        )
    except requests.RequestException as exc:
        raise CrossmintApiError(f"No se pudo conectar con Crossmint: {exc}") from exc

    if response.status_code >= 400:
        raise CrossmintApiError(
            f"Crossmint API error on {method} {url}",
            status_code=response.status_code,
            details=_safe_json(response),
        )

    return _safe_json(response)



def _extract_error_message(details: Any) -> str:
    if isinstance(details, dict):
        message = details.get("message")
        if isinstance(message, str):
            return message
    return ""



def ensure_wallet_linked(cfg: OnrampConfig) -> None:
    link_url = (
        f"{cfg.users_base_url}/users/email:{cfg.recipient_user_email}"
        f"/linked-wallets/{cfg.recipient_wallet_address}"
    )

    payload = {
        "chain": cfg.recipient_chain,
    }

    try:
        call_crossmint(
            method="PUT",
            url=link_url,
            server_key=cfg.server_key,
            payload=payload,
        )
    except CrossmintApiError as exc:
        message = _extract_error_message(exc.details).lower()

        if "already linked to a different user" in message:
            raise CrossmintApiError(
                "La wallet de destino ya está vinculada a otro usuario de Crossmint.",
                status_code=exc.status_code,
                details=exc.details,
            ) from exc

        if "already linked" in message:
            return

        raise



def create_onramp_order(
    cfg: OnrampConfig,
    *,
    amount: Decimal | str | float | int,
) -> dict[str, Any]:
    payload = {
        "lineItems": [
            {
                "tokenLocator": cfg.token_locator,
                "executionParameters": {
                    "mode": "exact-in",
                    "amount": _format_amount(amount),
                },
            }
        ],
        "payment": {
            "method": cfg.payment_method,
            "receiptEmail": cfg.recipient_user_email,
        },
        "recipient": {
            "walletAddress": cfg.recipient_wallet_address,
        },
    }

    data = call_crossmint(
        method="POST",
        url=f"{cfg.orders_base_url}/orders",
        server_key=cfg.server_key,
        payload=payload,
    )

    if not isinstance(data, dict):
        raise CrossmintApiError("Formato inesperado al crear pago en Crossmint")

    return data



def get_onramp_order(cfg: OnrampConfig, *, payment_id: str) -> dict[str, Any]:
    data = call_crossmint(
        method="GET",
        url=f"{cfg.orders_base_url}/orders/{payment_id}",
        server_key=cfg.server_key,
    )

    if not isinstance(data, dict):
        raise CrossmintApiError("Formato inesperado al consultar pago en Crossmint")

    return data



def extract_order_payload(data: dict[str, Any]) -> dict[str, Any]:
    nested = data.get("order") if isinstance(data.get("order"), dict) else None
    return nested if nested is not None else data



def extract_payment_status(order_payload: dict[str, Any]) -> str:
    payment = order_payload.get("payment") if isinstance(order_payload.get("payment"), dict) else {}
    return str(payment.get("status") or "").strip().lower()



def extract_checkout(order_payload: dict[str, Any]) -> dict[str, Any] | None:
    payment = order_payload.get("payment") if isinstance(order_payload.get("payment"), dict) else {}
    preparation = payment.get("preparation") if isinstance(payment.get("preparation"), dict) else {}

    public_key = preparation.get("checkoutcomPublicKey")
    session = preparation.get("checkoutcomPaymentSession")

    if not public_key and not session:
        return None

    return {
        "public_key": str(public_key) if public_key else None,
        "session": session if isinstance(session, dict) else None,
    }



def extract_kyc(order_payload: dict[str, Any]) -> dict[str, Any] | None:
    payment = order_payload.get("payment") if isinstance(order_payload.get("payment"), dict) else {}
    preparation = payment.get("preparation") if isinstance(payment.get("preparation"), dict) else {}
    kyc = preparation.get("kyc")

    if not isinstance(kyc, dict):
        return None

    required_keys = {"templateId", "referenceId", "environmentId"}
    if not required_keys.issubset(set(kyc.keys())):
        return None

    return {
        "templateId": str(kyc.get("templateId")),
        "referenceId": str(kyc.get("referenceId")),
        "environmentId": str(kyc.get("environmentId")),
    }



def extract_failure_reason(order_payload: dict[str, Any]) -> dict[str, str | None] | None:
    payment = order_payload.get("payment") if isinstance(order_payload.get("payment"), dict) else {}
    failure_reason = payment.get("failureReason") if isinstance(payment.get("failureReason"), dict) else None

    if not failure_reason:
        return None

    code = failure_reason.get("code")
    message = failure_reason.get("message")

    if code is None and message is None:
        return None

    return {
        "code": str(code) if code is not None else None,
        "message": str(message) if message is not None else None,
    }



def extract_amount_currency(order_payload: dict[str, Any]) -> tuple[Decimal, str]:
    quote = order_payload.get("quote") if isinstance(order_payload.get("quote"), dict) else {}
    total_price = quote.get("totalPrice") if isinstance(quote.get("totalPrice"), dict) else {}

    amount_raw = total_price.get("amount", "0")
    currency_raw = total_price.get("currency", "USD")

    try:
        amount = Decimal(str(amount_raw))
    except (InvalidOperation, ValueError):
        amount = Decimal("0")

    currency = str(currency_raw or "USD").upper()
    return amount, currency
