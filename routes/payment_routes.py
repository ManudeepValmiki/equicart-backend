from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.payment_service import PaymentService
from schemas.payment_schema import PaymentCreate
from middleware.auth_middleware import get_current_user, require_admin
from models.user_model import User
from utils.response_handler import success_response, created_response
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["Payments"])


class ConfirmPaymentRequest(BaseModel):
    transaction_id: str


class FailPaymentRequest(BaseModel):
    reason: str


@router.post("/initiate", status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a payment for an order."""
    service = PaymentService(db)
    result = await service.initiate_payment(data=data, user_id=current_user.id)
    return created_response(
        data=result.model_dump(mode="json"),
        message="Payment initiated",
    )


@router.post("/{payment_id}/confirm")
async def confirm_payment(
    payment_id: UUID,
    body: ConfirmPaymentRequest,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin / gateway webhook: mark a payment as completed."""
    service = PaymentService(db)
    payment = await service.confirm_payment(
        payment_id=payment_id, transaction_id=body.transaction_id
    )
    return success_response(data=payment.model_dump(mode="json"), message="Payment confirmed")


@router.post("/{payment_id}/fail")
async def fail_payment(
    payment_id: UUID,
    body: FailPaymentRequest,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin / gateway webhook: mark a payment as failed."""
    service = PaymentService(db)
    payment = await service.fail_payment(payment_id=payment_id, reason=body.reason)
    return success_response(data=payment.model_dump(mode="json"), message="Payment marked as failed")


@router.get("/{payment_id}")
async def get_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment details by ID."""
    service = PaymentService(db)
    payment = await service.get_payment(payment_id)
    return success_response(data=payment.model_dump(mode="json"))


@router.get("/order/{order_id}")
async def get_payment_by_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment details for a specific order."""
    service = PaymentService(db)
    payment = await service.get_payment_by_order(order_id)
    return success_response(data=payment.model_dump(mode="json"))
