from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from schemas.order_schema import OrderCreate, OrderResponse, OrderUpdate
from models.order_model import OrderStatus
from exceptions.custom_exception import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)

    async def create_order(self, user_id: UUID, data: OrderCreate) -> OrderResponse:
        enriched_items = []
        total_amount = 0.0

        for item in data.items:
            product = await self.product_repo.get_by_id(item.product_id)
            if not product:
                raise NotFoundException(detail=f"Product {item.product_id} not found")
            if not product.is_active:
                raise BadRequestException(detail=f"Product '{product.name}' is not available")
            if product.stock_quantity < item.quantity:
                raise BadRequestException(
                    detail=f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}"
                )
            unit_price = float(product.price)
            subtotal = unit_price * item.quantity
            total_amount += subtotal
            enriched_items.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                }
            )

        order = await self.repo.create(user_id=user_id, data=data, total_amount=total_amount)
        await self.repo.add_items(order.id, enriched_items)
        order = await self.repo.get_by_id(order.id)
        return OrderResponse.model_validate(order)

    async def get_order(self, order_id: UUID, user_id: UUID, is_admin: bool = False) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(detail="Order not found")
        if not is_admin and order.user_id != user_id:
            raise ForbiddenException(detail="Access to this order is not allowed")
        return OrderResponse.model_validate(order)

    async def list_user_orders(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> List[OrderResponse]:
        orders = await self.repo.get_by_user(user_id=user_id, skip=skip, limit=limit)
        return [OrderResponse.model_validate(o) for o in orders]

    async def list_all_orders(self, skip: int = 0, limit: int = 20) -> List[OrderResponse]:
        orders = await self.repo.get_all(skip=skip, limit=limit)
        return [OrderResponse.model_validate(o) for o in orders]

    async def update_order_status(
        self, order_id: UUID, status: OrderStatus
    ) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(detail="Order not found")
        updated = await self.repo.update_status(order_id, status)
        return OrderResponse.model_validate(updated)

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise NotFoundException(detail="Order not found")
        if order.user_id != user_id:
            raise ForbiddenException()
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise BadRequestException(detail="Order cannot be cancelled at this stage")
        updated = await self.repo.update_status(order_id, OrderStatus.CANCELLED)
        return OrderResponse.model_validate(updated)
