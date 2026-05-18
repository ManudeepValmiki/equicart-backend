from typing import Optional, List
from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from models.order_model import Order, OrderItem, OrderStatus
from schemas.order_schema import OrderCreate


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, order_id: UUID) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> List[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(self, skip: int = 0, limit: int = 20) -> List[Order]:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, user_id: UUID, data: OrderCreate, total_amount: float) -> Order:
        order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        order = Order(
            order_number=order_number,
            user_id=user_id,
            shipping_address=data.shipping_address,
            notes=data.notes,
            total_amount=total_amount,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    async def add_items(self, order_id: UUID, items: list) -> None:
        for item in items:
            order_item = OrderItem(
                order_id=order_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"],
            )
            self.db.add(order_item)
        await self.db.flush()

    async def update_status(self, order_id: UUID, status: OrderStatus) -> Optional[Order]:
        await self.db.execute(
            update(Order).where(Order.id == order_id).values(status=status)
        )
        return await self.get_by_id(order_id)
