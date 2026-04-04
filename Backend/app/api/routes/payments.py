from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.security import get_current_admin
from app.api.dependencies.db import get_db
from app.controllers import payments as payments_controller
from app.schemas.payments import PaymentCreateRequest, PaymentStatusResponse, PaymentSyncSummaryResponse


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create", response_model=PaymentStatusResponse, status_code=201)
async def create_payment(
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
):
    return payments_controller.crear_pago_pedido(db, payload=payload)


@router.get("/session/{payment_token}", response_model=PaymentStatusResponse)
async def get_payment_status_by_token(
    payment_token: str,
    sync_order: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    return payments_controller.obtener_estado_pago_por_token(
        db,
        payment_token=payment_token,
        sync_order=sync_order,
    )


@router.get("/sync/summary", response_model=PaymentSyncSummaryResponse)
async def get_payment_sync_summary(
    limit: int = Query(default=50, ge=1, le=100),
    sync_order: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    _ = admin
    return payments_controller.obtener_resumen_sincronizacion_pagos(
        db,
        limit=limit,
        sync_order=sync_order,
    )


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: str,
    pedido_id: int | None = Query(default=None, ge=1),
    referencia: str | None = Query(default=None, min_length=8, max_length=80),
    sync_order: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    return payments_controller.obtener_estado_pago(
        db,
        payment_id=payment_id,
        pedido_id=pedido_id,
        referencia=referencia,
        sync_order=sync_order,
    )
