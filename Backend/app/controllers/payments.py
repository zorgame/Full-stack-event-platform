from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.payments import PaymentCreateRequest, PaymentStatusResponse
from app.schemas.payments import PaymentSyncSummaryResponse
from app.services import payments as payments_service
from app.services.crossmint_onramp import CrossmintApiError


logger = logging.getLogger("tickets_api")

def crear_pago_pedido(db: Session, *, payload: PaymentCreateRequest) -> PaymentStatusResponse:
    try:
        return payments_service.create_payment_for_order(
            db,
            pedido_id=payload.pedido_id,
            referencia=payload.referencia,
            acepta_terminos=payload.acepta_terminos,
        )
    except ValueError as exc:
        logger.warning("Error de negocio creando pago Crossmint: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CrossmintApiError as exc:
        logger.warning("Error de proveedor creando pago Crossmint: %s", exc)
        detail = {
            "message": str(exc),
            "status_code": exc.status_code,
        }
        if settings.debug:
            detail["details"] = exc.details

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except Exception as exc:
        logger.exception("Error inesperado creando pago Crossmint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno creando pago",
        ) from exc



def obtener_estado_pago(
    db: Session,
    *,
    payment_id: str,
    pedido_id: int | None = None,
    referencia: str | None = None,
    sync_order: bool = True,
) -> PaymentStatusResponse:
    try:
        return payments_service.get_payment_status(
            db,
            payment_id=payment_id,
            pedido_id=pedido_id,
            referencia=referencia,
            sync_order=sync_order,
        )
    except ValueError as exc:
        logger.warning("Error de negocio consultando pago Crossmint: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CrossmintApiError as exc:
        logger.warning("Error de proveedor consultando pago Crossmint: %s", exc)
        detail = {
            "message": str(exc),
            "status_code": exc.status_code,
        }
        if settings.debug:
            detail["details"] = exc.details

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except Exception as exc:
        logger.exception("Error inesperado consultando pago Crossmint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno consultando pago",
        ) from exc


def obtener_estado_pago_por_token(
    db: Session,
    *,
    payment_token: str,
    sync_order: bool = True,
) -> PaymentStatusResponse:
    try:
        return payments_service.get_payment_status_by_token(
            db,
            payment_token=payment_token,
            sync_order=sync_order,
        )
    except ValueError as exc:
        logger.warning("Error de negocio consultando pago por token: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CrossmintApiError as exc:
        logger.warning("Error de proveedor consultando pago por token: %s", exc)
        detail = {
            "message": str(exc),
            "status_code": exc.status_code,
        }
        if settings.debug:
            detail["details"] = exc.details

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except Exception as exc:
        logger.exception("Error inesperado consultando pago por token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno consultando pago",
        ) from exc


def obtener_resumen_sincronizacion_pagos(
    db: Session,
    *,
    limit: int = 50,
    sync_order: bool = False,
) -> PaymentSyncSummaryResponse:
    try:
        return payments_service.get_payment_sync_summary(
            db,
            limit=limit,
            sync_order=sync_order,
        )
    except ValueError as exc:
        logger.warning("Error de negocio obteniendo resumen de sincronizacion: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CrossmintApiError as exc:
        logger.warning("Error de proveedor en resumen de sincronizacion: %s", exc)
        detail = {
            "message": str(exc),
            "status_code": exc.status_code,
        }
        if settings.debug:
            detail["details"] = exc.details

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc
    except Exception as exc:
        logger.exception("Error inesperado en resumen de sincronizacion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno obteniendo resumen de sincronizacion",
        ) from exc