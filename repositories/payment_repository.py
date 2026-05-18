from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.payment_model import Payment, PaymentStatus
from schemas.payment_schema import PaymentCreate, PaymentUpdate


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order_id(self, order_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: PaymentCreate, amount: float) -> Payment:
        payment = Payment(
            order_id=data.order_id,
            amount=amount,
            currency=data.currency,
            method=data.method,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def update(self, payment_id: UUID, data: PaymentUpdate) -> Optional[Payment]:
        values = data.model_dump(exclude_none=True)
        if not values:
            return await self.get_by_id(payment_id)
        await self.db.execute(
            update(Payment).where(Payment.id == payment_id).values(**values)
        )
        return await self.get_by_id(payment_id)

    async def update_status(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        transaction_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> Optional[Payment]:
        values: dict = {"status": status}
        if transaction_id:
            values["transaction_id"] = transaction_id
        if failure_reason:
            values["failure_reason"] = failure_reason
        await self.db.execute(
            update(Payment).where(Payment.id == payment_id).values(**values)
        )
        return await self.get_by_id(payment_id)
