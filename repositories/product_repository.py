from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from models.product_model import Product, Category
from schemas.product_schema import ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[UUID] = None,
        active_only: bool = True,
    ) -> List[Product]:
        query = select(Product).options(selectinload(Product.category))
        if active_only:
            query = query.where(Product.is_active == True)
        if category_id:
            query = query.where(Product.category_id == category_id)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, product_id: UUID, data: ProductUpdate) -> Optional[Product]:
        values = data.model_dump(exclude_none=True)
        if not values:
            return await self.get_by_id(product_id)
        await self.db.execute(
            update(Product).where(Product.id == product_id).values(**values)
        )
        return await self.get_by_id(product_id)

    async def delete(self, product_id: UUID) -> None:
        await self.db.execute(
            update(Product).where(Product.id == product_id).values(is_active=False)
        )


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 50) -> List[Category]:
        result = await self.db.execute(
            select(Category).where(Category.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, data: CategoryCreate) -> Category:
        category = Category(**data.model_dump())
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: UUID, data: CategoryUpdate) -> Optional[Category]:
        values = data.model_dump(exclude_none=True)
        if not values:
            return await self.get_by_id(category_id)
        await self.db.execute(
            update(Category).where(Category.id == category_id).values(**values)
        )
        return await self.get_by_id(category_id)
