from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from decimal import Decimal
import re

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import constants
from app.core.config import settings
from app.models import Pedidos
from app.repositories import usuarios as usuarios_repo
from app.schemas.payments import (
    PaymentAccessCredentials,
    PaymentFailureReason,
    PaymentOrderSummary,
    PaymentSyncMismatchItem,
    PaymentSyncSummaryResponse,
    PaymentStatusResponse,
    PaymentSupportData,
)
from app.schemas.usuarios import UsuarioCreate
from app.services import pedidos as pedidos_service
from app.services import usuarios as usuarios_service
from app.services.crossmint_onramp import (
    CrossmintApiError,
    create_onramp_order,
    ensure_wallet_linked,
    extract_amount_currency,
    extract_checkout,
    extract_failure_reason,
    extract_kyc,
    extract_order_payload,
    extract_payment_status,
    get_onramp_config,
    get_onramp_order,
)
from app.services.user_access_emails import enviar_correo_acceso_pago
from app.utils.cache import cache_get_json, cache_set_json
from app.utils.security import generar_password_segura


logger = logging.getLogger("tickets_api")

PAYMENT_TOKEN_PURPOSE = "payment-session-v1"
PAYMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{6,160}$")


def _normalize_payment_id(value: str, *, field_name: str = "payment_id") -> str:
    payment_id = str(value or "").strip()
    if not payment_id:
        raise ValueError(f"{field_name} es requerido")

    if "/" in payment_id or "?" in payment_id or "#" in payment_id:
        raise ValueError(f"{field_name} inválido")

    if not PAYMENT_ID_PATTERN.fullmatch(payment_id):
        raise ValueError(f"{field_name} inválido")

    return payment_id


def _payment_session_cache_key(*, pedido_id: int) -> str:
    return f"{constants.CACHE_KEY_PAYMENT_SESSION_PREFIX}{int(pedido_id)}"


def _payment_session_cache_ttl_seconds() -> int:
    token_ttl_seconds = max(5, int(settings.payment_link_token_ttl_minutes or 180)) * 60
    return max(token_ttl_seconds, 60 * 60 * 24 * 7)


def _record_payment_session(*, pedido_id: int, referencia: str, payment_id: str) -> None:
    payment_id_normalizado = _normalize_payment_id(payment_id)
    cache_set_json(
        _payment_session_cache_key(pedido_id=pedido_id),
        {
            "pedido_id": int(pedido_id),
            "referencia": str(referencia or "").strip(),
            "payment_id": payment_id_normalizado,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        _payment_session_cache_ttl_seconds(),
    )


def _split_nombre_apellido(nombre_completo: str | None) -> tuple[str, str]:
    partes = [parte for parte in str(nombre_completo or "").strip().split() if parte]
    if not partes:
        return "Cliente", "Nova"
    if len(partes) == 1:
        return partes[0], "Nova"
    return partes[0], " ".join(partes[1:])


def _build_payment_token(*, payment_id: str, pedido_id: int, referencia: str) -> str:
    ttl_minutes = max(5, int(settings.payment_link_token_ttl_minutes or 180))
    safe_payment_id = _normalize_payment_id(payment_id)
    payload = {
        "purpose": PAYMENT_TOKEN_PURPOSE,
        "payment_id": safe_payment_id,
        "pedido_id": int(pedido_id),
        "referencia": str(referencia or "").strip(),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _decode_payment_token(payment_token: str) -> tuple[str, int, str]:
    token = str(payment_token or "").strip()
    if not token:
        raise ValueError("payment_token es requerido")

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("payment_token inválido o expirado") from exc

    if str(payload.get("purpose") or "").strip() != PAYMENT_TOKEN_PURPOSE:
        raise ValueError("payment_token inválido")

    payment_id = _normalize_payment_id(payload.get("payment_id") or "")
    referencia = str(payload.get("referencia") or "").strip()

    try:
        pedido_id = int(payload.get("pedido_id"))
    except (TypeError, ValueError) as exc:
        raise ValueError("payment_token inválido") from exc

    if pedido_id <= 0 or not referencia:
        raise ValueError("payment_token inválido")

    return payment_id, pedido_id, referencia


def _ensure_usuario_para_pedido_pagado(
    db: Session,
    *,
    pedido,
) -> tuple[int | None, dict | None]:
    correo = str(pedido.correo_electronico or "").strip().lower()
    if not correo:
        return None, None

    usuario_existente = usuarios_repo.get_usuario_por_email(db, correo)
    if usuario_existente is not None:
        if not bool(usuario_existente.is_active):
            usuario_existente.is_active = True
            db.add(usuario_existente)
            db.commit()
            db.refresh(usuario_existente)
        return int(usuario_existente.id), None

    nombre, apellido = _split_nombre_apellido(pedido.nombre_completo)
    password_temporal = generar_password_segura(20)

    try:
        usuario_creado = usuarios_service.crear_usuario(
            db,
            UsuarioCreate(
                email=correo,
                telefono=str(pedido.telefono or "").strip() or None,
                nombre=nombre,
                apellido=apellido,
                pais=str(pedido.pais or "").strip() or None,
                password=password_temporal,
                is_admin=False,
            ),
        )
    except Exception:
        usuario_existente = usuarios_repo.get_usuario_por_email(db, correo)
        if usuario_existente is None:
            raise

        if not bool(usuario_existente.is_active):
            usuario_existente.is_active = True
            db.add(usuario_existente)
            db.commit()
            db.refresh(usuario_existente)

        return int(usuario_existente.id), None

    return int(usuario_creado.id), {
        "email": usuario_creado.email,
        "password": password_temporal,
    }

PAYMENT_STATUS_FAILED = {
    "failed",
    "payment-failed",
    "crypto-payer-insufficient-funds",
    "manual-kyc",
    "rejected-kyc",
}

PAYMENT_STATUS_CANCELED = {
    "cancelled",
    "canceled",
    "expired",
    "abandoned",
}

PAYMENT_STATUS_PENDING = {
    "awaiting-payment",
    "requires-kyc",
    "pending-kyc-review",
    "requires-recipient-verification",
}



def _target_pedido_status_from_payment(payment_status: str) -> str | None:
    normalized = str(payment_status or "").strip().lower()

    if normalized == "completed":
        return constants.PEDIDO_ESTADO_PAGADO

    if normalized in PAYMENT_STATUS_CANCELED:
        return constants.PEDIDO_ESTADO_CANCELADO

    if normalized in PAYMENT_STATUS_FAILED:
        return constants.PEDIDO_ESTADO_FALLIDO

    if normalized in PAYMENT_STATUS_PENDING:
        return constants.PEDIDO_ESTADO_PENDIENTE

    return None



def _build_order_summary(
    *,
    pedido_id: int,
    pedido_referencia: str,
    pedido_estado: str,
    total: Decimal,
    currency: str,
) -> PaymentOrderSummary:
    return PaymentOrderSummary(
        id=pedido_id,
        referencia=pedido_referencia,
        estado=pedido_estado,
        total=Decimal(str(total or "0")),
        currency=currency or "USD",
    )



def _build_payment_response(
    *,
    payment_id: str,
    payment_token: str | None,
    payment_status: str,
    pedido_summary: PaymentOrderSummary | None,
    checkout_payload: dict | None,
    kyc_payload: dict | None,
    failure_reason_payload: dict | None,
    access_credentials_payload: dict | None,
    support_whatsapp: str,
    raw_payload: dict | None,
) -> PaymentStatusResponse:
    failure_reason = None
    if isinstance(failure_reason_payload, dict):
        failure_reason = PaymentFailureReason(
            code=failure_reason_payload.get("code"),
            message=failure_reason_payload.get("message"),
        )

    access_credentials = None
    if isinstance(access_credentials_payload, dict) and access_credentials_payload.get("email"):
        access_credentials = PaymentAccessCredentials(
            email=str(access_credentials_payload.get("email")),
            password=access_credentials_payload.get("password"),
        )

    return PaymentStatusResponse(
        payment_id=payment_id,
        payment_token=payment_token,
        status=payment_status,
        order=pedido_summary,
        checkout=checkout_payload,
        kyc=kyc_payload,
        failure_reason=failure_reason,
        access_credentials=access_credentials,
        support=PaymentSupportData(whatsapp_number=support_whatsapp or None),
        raw=raw_payload,
    )

def _sync_pedido_state(
    db: Session,
    *,
    pedido_id: int,
    payment_status: str,
    usuario_id_asignacion: int | None = None,
) -> None:
    target_status = _target_pedido_status_from_payment(payment_status)
    if target_status is None:
        return

    pedido_actual = pedidos_service.get_pedido(db, pedido_id=pedido_id)
    if pedido_actual is None:
        return

    estado_actual = str(pedido_actual.estado or "").strip().lower()
    if estado_actual == target_status:
        if (
            target_status == constants.PEDIDO_ESTADO_PAGADO
            and usuario_id_asignacion is not None
            and int(pedido_actual.usuario_id or 0) != int(usuario_id_asignacion)
        ):
            try:
                pedidos_service.actualizar_estado_pedido(
                    db,
                    pedido_id=pedido_id,
                    nuevo_estado=target_status,
                    usuario_id_asignacion=usuario_id_asignacion,
                )
            except ValueError as exc:
                logger.warning(
                    "No se pudo completar asignación de usuario en pedido pagado %s: %s",
                    pedido_id,
                    exc,
                )
        return

    if estado_actual == constants.PEDIDO_ESTADO_PAGADO and target_status != constants.PEDIDO_ESTADO_PAGADO:
        return

    try:
        pedidos_service.actualizar_estado_pedido(
            db,
            pedido_id=pedido_id,
            nuevo_estado=target_status,
            usuario_id_asignacion=(
                usuario_id_asignacion if target_status == constants.PEDIDO_ESTADO_PAGADO else None
            ),
        )
    except ValueError as exc:
        logger.warning(
            "No se pudo sincronizar estado de pedido %s con pago (%s): %s",
            pedido_id,
            payment_status,
            exc,
        )



def create_payment_for_order(
    db: Session,
    *,
    pedido_id: int,
    referencia: str,
    acepta_terminos: bool,
) -> PaymentStatusResponse:
    pedido = pedidos_service.get_pedido(db, pedido_id=pedido_id)
    if pedido is None:
        raise ValueError("Pedido no encontrado")

    referencia_normalizada = str(referencia or "").strip()
    if not referencia_normalizada:
        raise ValueError("La referencia es obligatoria")

    if not bool(acepta_terminos):
        raise ValueError("Debes aceptar los términos y condiciones para continuar")

    if str(pedido.referencia).strip() != referencia_normalizada:
        raise ValueError("La referencia del pedido no coincide")

    pedido_estado = str(pedido.estado or "").strip().lower()
    if pedido_estado == constants.PEDIDO_ESTADO_PAGADO:
        raise ValueError("El pedido ya se encuentra pagado")

    if pedido_estado == constants.PEDIDO_ESTADO_CANCELADO:
        raise ValueError("El pedido está cancelado y no admite nuevos pagos")

    cfg = get_onramp_config(strict=True)

    ensure_wallet_linked(cfg)

    create_payload = create_onramp_order(
        cfg,
        amount=Decimal(str(pedido.total or "0")),
    )

    order_payload = extract_order_payload(create_payload)
    raw_payment_id = str(order_payload.get("orderId") or "").strip()
    if not raw_payment_id:
        raise CrossmintApiError("Crossmint no devolvió un payment_id válido")

    try:
        payment_id = _normalize_payment_id(raw_payment_id)
    except ValueError as exc:
        raise CrossmintApiError("Crossmint devolvió un payment_id inválido") from exc

    _record_payment_session(
        pedido_id=pedido_id,
        referencia=referencia_normalizada,
        payment_id=payment_id,
    )

    payment_status = extract_payment_status(order_payload)
    payment_token = _build_payment_token(
        payment_id=payment_id,
        pedido_id=pedido_id,
        referencia=referencia_normalizada,
    )
    checkout_payload = extract_checkout(order_payload)
    kyc_payload = extract_kyc(order_payload)
    failure_reason_payload = extract_failure_reason(order_payload)
    amount, currency = extract_amount_currency(order_payload)

    _sync_pedido_state(
        db,
        pedido_id=pedido_id,
        payment_status=payment_status,
    )

    pedido_actualizado = pedidos_service.get_pedido(db, pedido_id=pedido_id) or pedido

    pedido_summary = _build_order_summary(
        pedido_id=int(pedido_actualizado.id),
        pedido_referencia=str(pedido_actualizado.referencia),
        pedido_estado=str(pedido_actualizado.estado),
        total=amount if amount > 0 else Decimal(str(pedido_actualizado.total or "0")),
        currency=currency or "USD",
    )

    return _build_payment_response(
        payment_id=payment_id,
        payment_token=payment_token,
        payment_status=payment_status,
        pedido_summary=pedido_summary,
        checkout_payload=checkout_payload,
        kyc_payload=kyc_payload,
        failure_reason_payload=failure_reason_payload,
        access_credentials_payload=None,
        support_whatsapp=cfg.support_whatsapp,
        raw_payload=None,
    )



def get_payment_status(
    db: Session,
    *,
    payment_id: str,
    pedido_id: int | None = None,
    referencia: str | None = None,
    sync_order: bool = True,
) -> PaymentStatusResponse:
    safe_payment_id = _normalize_payment_id(payment_id)

    if sync_order and pedido_id is None:
        raise ValueError("pedido_id es requerido cuando sync_order=true")

    if referencia is not None and not str(referencia).strip():
        raise ValueError("La referencia es inválida")

    cfg = get_onramp_config(strict=True)

    order_payload = extract_order_payload(
        get_onramp_order(cfg, payment_id=safe_payment_id),
    )

    status = extract_payment_status(order_payload)
    checkout_payload = extract_checkout(order_payload)
    kyc_payload = extract_kyc(order_payload)
    failure_reason_payload = extract_failure_reason(order_payload)
    amount, currency = extract_amount_currency(order_payload)

    pedido_summary = None
    access_credentials_payload = None
    referencia_token = str(referencia or "").strip()
    if pedido_id is not None:
        pedido = pedidos_service.get_pedido(db, pedido_id=pedido_id)
        if pedido is None:
            raise ValueError("Pedido no encontrado")

        referencia_normalizada = str(referencia or "").strip()
        if referencia_normalizada and str(pedido.referencia).strip() != referencia_normalizada:
            raise ValueError("La referencia del pedido no coincide")

        referencia_token = str(pedido.referencia or "").strip()

        if sync_order:
            usuario_id_asignacion = None
            if _target_pedido_status_from_payment(status) == constants.PEDIDO_ESTADO_PAGADO:
                usuario_id_asignacion, access_credentials_payload = _ensure_usuario_para_pedido_pagado(
                    db,
                    pedido=pedido,
                )

            _sync_pedido_state(
                db,
                pedido_id=pedido_id,
                payment_status=status,
                usuario_id_asignacion=usuario_id_asignacion,
            )
            pedido = pedidos_service.get_pedido(db, pedido_id=pedido_id) or pedido

            if (
                access_credentials_payload is not None
                and access_credentials_payload.get("password")
                and str(pedido.estado or "").strip().lower() == constants.PEDIDO_ESTADO_PAGADO
            ):
                enviar_correo_acceso_pago(
                    pedido=pedido,
                    email=access_credentials_payload.get("email") or "",
                    password_temporal=access_credentials_payload.get("password"),
                )

        pedido_summary = _build_order_summary(
            pedido_id=int(pedido.id),
            pedido_referencia=str(pedido.referencia),
            pedido_estado=str(pedido.estado),
            total=amount if amount > 0 else Decimal(str(pedido.total or "0")),
            currency=currency or "USD",
        )

    response_payment_id = _normalize_payment_id(str(order_payload.get("orderId") or safe_payment_id))
    payment_token = None
    if pedido_id is not None and referencia_token:
        payment_token = _build_payment_token(
            payment_id=response_payment_id,
            pedido_id=pedido_id,
            referencia=referencia_token,
        )

    return _build_payment_response(
        payment_id=response_payment_id,
        payment_token=payment_token,
        payment_status=status,
        pedido_summary=pedido_summary,
        checkout_payload=checkout_payload,
        kyc_payload=kyc_payload,
        failure_reason_payload=failure_reason_payload,
        access_credentials_payload=access_credentials_payload,
        support_whatsapp=cfg.support_whatsapp,
        raw_payload=None,
    )


def get_payment_status_by_token(
    db: Session,
    *,
    payment_token: str,
    sync_order: bool = True,
) -> PaymentStatusResponse:
    payment_id, pedido_id, referencia = _decode_payment_token(payment_token)
    return get_payment_status(
        db,
        payment_id=payment_id,
        pedido_id=pedido_id,
        referencia=referencia,
        sync_order=sync_order,
    )


def get_payment_sync_summary(
    db: Session,
    *,
    limit: int = 50,
    sync_order: bool = False,
) -> PaymentSyncSummaryResponse:
    scope_limit = max(1, min(100, int(limit or 50)))
    pedidos_rows = db.execute(
        select(
            Pedidos.id,
            Pedidos.referencia,
            Pedidos.estado,
        )
        .order_by(Pedidos.id.desc())
        .limit(scope_limit)
    ).all()

    provider_available = True
    provider_message: str | None = None
    provider_cfg = None
    try:
        provider_cfg = get_onramp_config(strict=True)
    except ValueError as exc:
        provider_available = False
        provider_message = str(exc)

    with_payment_session = 0
    without_payment_session = 0
    compared_orders = 0
    in_sync = 0
    out_of_sync = 0
    provider_errors = 0
    mismatches: list[PaymentSyncMismatchItem] = []

    for pedido_id, referencia, estado_pedido in pedidos_rows:
        pedido_id = int(pedido_id)
        referencia = str(referencia or "").strip()
        estado_pedido = str(estado_pedido or "").strip().lower()

        raw_session_payload = cache_get_json(_payment_session_cache_key(pedido_id=pedido_id))
        session_payload = raw_session_payload if isinstance(raw_session_payload, dict) else {}

        raw_payment_id = str(session_payload.get("payment_id") or "").strip()
        try:
            payment_id = _normalize_payment_id(raw_payment_id) if raw_payment_id else ""
        except ValueError:
            payment_id = ""
            if len(mismatches) < 20:
                mismatches.append(
                    PaymentSyncMismatchItem(
                        pedido_id=pedido_id,
                        referencia=referencia,
                        payment_id=raw_payment_id,
                        estado_pedido=estado_pedido,
                        estado_crossmint=None,
                        estado_objetivo=None,
                        reason="invalid_payment_id",
                        detail="payment_id almacenado inválido",
                    )
                )

        if not payment_id:
            without_payment_session += 1
            continue

        with_payment_session += 1

        if not provider_available or provider_cfg is None:
            continue

        try:
            if sync_order:
                payment_status_response = get_payment_status(
                    db,
                    payment_id=payment_id,
                    pedido_id=pedido_id,
                    referencia=referencia,
                    sync_order=True,
                )
                payment_status = str(payment_status_response.status or "").strip().lower()
            else:
                order_payload = extract_order_payload(
                    get_onramp_order(provider_cfg, payment_id=payment_id),
                )
                payment_status = extract_payment_status(order_payload)
        except (CrossmintApiError, ValueError) as exc:
            provider_errors += 1
            if len(mismatches) < 20:
                mismatches.append(
                    PaymentSyncMismatchItem(
                        pedido_id=pedido_id,
                        referencia=referencia,
                        payment_id=payment_id,
                        estado_pedido=estado_pedido,
                        estado_crossmint=None,
                        estado_objetivo=None,
                        reason="provider_error",
                        detail=str(exc),
                    )
                )
            continue

        compared_orders += 1
        estado_objetivo = _target_pedido_status_from_payment(payment_status)
        if estado_objetivo is not None and estado_objetivo == estado_pedido:
            in_sync += 1
            continue

        out_of_sync += 1
        reason = "state_mismatch"
        detail = None
        if estado_objetivo is None:
            reason = "unmapped_payment_status"
            detail = "El estado de Crossmint no tiene mapeo interno"

        if len(mismatches) < 20:
            mismatches.append(
                PaymentSyncMismatchItem(
                    pedido_id=pedido_id,
                    referencia=referencia,
                    payment_id=payment_id,
                    estado_pedido=estado_pedido,
                    estado_crossmint=payment_status,
                    estado_objetivo=estado_objetivo,
                    reason=reason,
                    detail=detail,
                )
            )

    return PaymentSyncSummaryResponse(
        provider_available=provider_available,
        provider_message=provider_message,
        sync_order_applied=bool(sync_order and provider_available),
        scope_limit=scope_limit,
        scanned_orders=len(pedidos_rows),
        with_payment_session=with_payment_session,
        without_payment_session=without_payment_session,
        compared_orders=compared_orders,
        in_sync=in_sync,
        out_of_sync=out_of_sync,
        provider_errors=provider_errors,
        mismatches=mismatches,
    )
