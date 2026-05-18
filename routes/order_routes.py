from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.order_service import OrderService
from schemas.order_schema import OrderCreate, OrderUpdate
from models.order_model import OrderStatus
from middleware.auth_middleware import get_current_user, require_admin
from models.user_model import User
from utils.response_handler import success_response, created_response

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a new order for the authenticated user."""
    service = OrderService(db)
    order = await service.create_order(user_id=current_user.id, data=data)
    return created_response(data=order.model_dump(mode="json"), message="Order placed successfully")


@router.get("/me")
async def list_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all orders for the authenticated user."""
    service = OrderService(db)
    orders = await service.list_user_orders(user_id=current_user.id, skip=skip, limit=limit)
    return success_response(data=[o.model_dump(mode="json") for o in orders])


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific order. Admins can access any order; customers only their own."""
    from models.user_model import UserRole
    is_admin = current_user.role == UserRole.ADMIN
    service = OrderService(db)
    order = await service.get_order(order_id=order_id, user_id=current_user.id, is_admin=is_admin)
    return success_response(data=order.model_dump(mode="json"))


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending or confirmed order."""
    service = OrderService(db)
    order = await service.cancel_order(order_id=order_id, user_id=current_user.id)
    return success_response(data=order.model_dump(mode="json"), message="Order cancelled")


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    status: OrderStatus,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: update the status of any order."""
    service = OrderService(db)
    order = await service.update_order_status(order_id=order_id, status=status)
    return success_response(data=order.model_dump(mode="json"), message="Order status updated")


@router.get("")
async def list_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all orders."""
    service = OrderService(db)
    orders = await service.list_all_orders(skip=skip, limit=limit)
    return success_response(data=[o.model_dump(mode="json") for o in orders])
