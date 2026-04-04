from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    pedido_id: int = Field(..., gt=0)
    referencia: str = Field(..., min_length=8, max_length=80)
    acepta_terminos: bool = Field(...)


class PaymentCheckoutPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    public_key: str | None = None
    session: dict[str, Any] | None = None


class PaymentKycPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    templateId: str
    referenceId: str
    environmentId: str


class PaymentFailureReason(BaseModel):
    code: str | None = None
    message: str | None = None


class PaymentOrderSummary(BaseModel):
    id: int
    referencia: str
    estado: str
    total: Decimal
    currency: str = "USD"


class PaymentSupportData(BaseModel):
    whatsapp_number: str | None = None


class PaymentAccessCredentials(BaseModel):
    email: str
    password: str | None = None


class PaymentSyncMismatchItem(BaseModel):
    pedido_id: int
    referencia: str
    payment_id: str
    estado_pedido: str
    estado_crossmint: str | None = None
    estado_objetivo: str | None = None
    reason: str
    detail: str | None = None


class PaymentSyncSummaryResponse(BaseModel):
    provider: Literal["crossmint"] = "crossmint"
    provider_available: bool
    provider_message: str | None = None
    sync_order_applied: bool = False
    scope_limit: int
    scanned_orders: int
    with_payment_session: int
    without_payment_session: int
    compared_orders: int
    in_sync: int
    out_of_sync: int
    provider_errors: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    mismatches: list[PaymentSyncMismatchItem] = Field(default_factory=list)


class PaymentStatusResponse(BaseModel):
    provider: Literal["crossmint"] = "crossmint"
    payment_id: str
    payment_token: str | None = None
    status: str
    order: PaymentOrderSummary | None = None
    checkout: PaymentCheckoutPayload | None = None
    kyc: PaymentKycPayload | None = None
    failure_reason: PaymentFailureReason | None = None
    access_credentials: PaymentAccessCredentials | None = None
    support: PaymentSupportData = Field(default_factory=PaymentSupportData)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    raw: dict[str, Any] | None = None
