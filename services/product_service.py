from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.product_repository import ProductRepository, CategoryRepository
from schemas.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from exceptions.custom_exception import NotFoundException, ConflictException


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)

    async def get_product(self, product_id: UUID) -> ProductResponse:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Product not found")
        return ProductResponse.model_validate(product)

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[UUID] = None,
    ) -> List[ProductResponse]:
        products = await self.repo.get_all(skip=skip, limit=limit, category_id=category_id)
        return [ProductResponse.model_validate(p) for p in products]

    async def create_product(self, data: ProductCreate) -> ProductResponse:
        existing = await self.repo.get_by_sku(data.sku)
        if existing:
            raise ConflictException(detail=f"Product with SKU '{data.sku}' already exists")
        if data.category_id:
            category = await self.category_repo.get_by_id(data.category_id)
            if not category:
                raise NotFoundException(detail="Category not found")
        product = await self.repo.create(data)
        return ProductResponse.model_validate(product)

    async def update_product(self, product_id: UUID, data: ProductUpdate) -> ProductResponse:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Product not found")
        updated = await self.repo.update(product_id, data)
        return ProductResponse.model_validate(updated)

    async def delete_product(self, product_id: UUID) -> None:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Product not found")
        await self.repo.delete(product_id)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def list_categories(self) -> List[CategoryResponse]:
        categories = await self.repo.get_all()
        return [CategoryResponse.model_validate(c) for c in categories]

    async def create_category(self, data: CategoryCreate) -> CategoryResponse:
        category = await self.repo.create(data)
        return CategoryResponse.model_validate(category)

    async def update_category(
        self, category_id: UUID, data: CategoryUpdate
    ) -> CategoryResponse:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise NotFoundException(detail="Category not found")
        updated = await self.repo.update(category_id, data)
        return CategoryResponse.model_validate(updated)
