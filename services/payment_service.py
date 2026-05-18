from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.payment_repository import PaymentRepository
from repositories.order_repository import OrderRepository
from schemas.payment_schema import PaymentCreate, PaymentResponse, PaymentInitiateResponse
from models.payment_model import PaymentStatus
from models.order_model import OrderStatus
from exceptions.custom_exception import (
    NotFoundException,
    BadRequestException,
    PaymentFailedException,
    ConflictException,
)


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)

    async def initiate_payment(
        self, data: PaymentCreate, user_id: UUID
    ) -> PaymentInitiateResponse:
        order = await self.order_repo.get_by_id(data.order_id)
        if not order:
            raise NotFoundException(detail="Order not found")
        if order.user_id != user_id:
            raise BadRequestException(detail="Order does not belong to this user")
        if order.status != OrderStatus.PENDING:
            raise BadRequestException(detail="Order is not in a payable state")

        existing = await self.repo.get_by_order_id(data.order_id)
        if existing and existing.status == PaymentStatus.COMPLETED:
            raise ConflictException(detail="Order has already been paid")

        payment = await self.repo.create(data, amount=float(order.total_amount))

        # In production, integrate with a payment gateway here and return gateway_url
        return PaymentInitiateResponse(
            payment_id=payment.id,
            order_id=order.id,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            gateway_url=None,
        )

    async def confirm_payment(
        self, payment_id: UUID, transaction_id: str
    ) -> PaymentResponse:
        payment = await self.repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException(detail="Payment not found")
        if payment.status == PaymentStatus.COMPLETED:
            raise ConflictException(detail="Payment already completed")

        # Simulate gateway verification — replace with real gateway call
        updated = await self.repo.update_status(
            payment_id,
            status=PaymentStatus.COMPLETED,
            transaction_id=transaction_id,
        )
        await self.order_repo.update_status(payment.order_id, OrderStatus.CONFIRMED)
        return PaymentResponse.model_validate(updated)

    async def fail_payment(self, payment_id: UUID, reason: str) -> PaymentResponse:
        payment = await self.repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException(detail="Payment not found")
        updated = await self.repo.update_status(
            payment_id,
            status=PaymentStatus.FAILED,
            failure_reason=reason,
        )
        return PaymentResponse.model_validate(updated)

    async def get_payment(self, payment_id: UUID) -> PaymentResponse:
        payment = await self.repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException(detail="Payment not found")
        return PaymentResponse.model_validate(payment)

    async def get_payment_by_order(self, order_id: UUID) -> PaymentResponse:
        payment = await self.repo.get_by_order_id(order_id)
        if not payment:
            raise NotFoundException(detail="Payment not found for this order")
        return PaymentResponse.model_validate(payment)
