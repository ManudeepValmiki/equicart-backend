from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.product_service import ProductService, CategoryService
from schemas.product_schema import ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate
from middleware.auth_middleware import get_current_user, require_seller
from models.user_model import User
from utils.response_handler import success_response, created_response

router = APIRouter(prefix="/products", tags=["Products"])
category_router = APIRouter(prefix="/categories", tags=["Categories"])


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("")
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    products = await service.list_products(skip=skip, limit=limit, category_id=category_id)
    return success_response(data=[p.model_dump(mode="json") for p in products])


@router.get("/{product_id}")
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.get_product(product_id)
    return success_response(data=product.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    _: User = Depends(require_seller),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    product = await service.create_product(data)
    return created_response(data=product.model_dump(mode="json"), message="Product created")


@router.patch("/{product_id}")
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    _: User = Depends(require_seller),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    product = await service.update_product(product_id, data)
    return success_response(data=product.model_dump(mode="json"), message="Product updated")


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    _: User = Depends(require_seller),
    db: AsyncSession = Depends(get_db),
):
    service = ProductService(db)
    await service.delete_product(product_id)


# ── Categories ────────────────────────────────────────────────────────────────

@category_router.get("")
async def list_categories(db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    categories = await service.list_categories()
    return success_response(data=[c.model_dump(mode="json") for c in categories])


@category_router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    _: User = Depends(require_seller),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.create_category(data)
    return created_response(data=category.model_dump(mode="json"), message="Category created")


@category_router.patch("/{category_id}")
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    _: User = Depends(require_seller),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.update_category(category_id, data)
    return success_response(data=category.model_dump(mode="json"), message="Category updated")
