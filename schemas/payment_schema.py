from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from models.payment_model import PaymentStatus, PaymentMethod


class PaymentCreate(BaseModel):
    order_id: UUID
    method: PaymentMethod
    currency: str = Field(default="INR", min_length=3, max_length=3)


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = Field(None, max_length=255)
    gateway_response: Optional[str] = None
    failure_reason: Optional[str] = None


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: PaymentMethod
    transaction_id: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentInitiateResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    method: PaymentMethod
    gateway_url: Optional[str] = None  # Redirect URL for gateway-based payments
