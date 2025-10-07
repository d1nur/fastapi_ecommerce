from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, update

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db

from app.models.products import Product as ProductModel
from app.models.categories import Category
from app.schemas import Product as ProductSchema, ProductCreate
from app.models.users import User as UserModel
from app.auth import get_current_seller


router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров.
    :return:
    """
    stmt = select(ProductModel).where(ProductModel.is_active == True)
    result = await db.scalars(stmt)
    products = result.all()
    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate,
                         db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Создает новый товар.
    :return:
    """
    stmt = select(Category).where(product.category_id == Category.id, Category.is_active == True)
    result = await db.scalars(stmt)
    is_id_exists = result.first()
    if is_id_exists is None:
        raise HTTPException(status_code=400, detail="Category not found")

    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    :param db:
    :param category_id:
    :return:
    """
    stmt = select(Category).where(Category.id == category_id, Category.is_active == True)
    result = await db.scalars(stmt)
    category = result.first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True)
    result_pbc = await db.scalars(stmt)
    products_by_category = result_pbc.all()
    return products_by_category


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    :param db:
    :param product_id:
    :return:
    """

    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)
    product = result.first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    stmt = select(Category).where(Category.id == product.category_id, Category.is_active == True)
    result_cat = await db.scalars(stmt)
    category = result_cat.first()
    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")
    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int,
                         product: ProductCreate,
                         db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Обновляет товар по его ID.
    :param db:
    :param product:
    :param product_id:
    :return:
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    stmt = select(Category).where(Category.id == product.category_id, Category.is_active == True)
    result_cat = await db.scalars(stmt)
    db_category = result_cat.first()
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category not found")
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: int,
                         db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Удаляет товар по его ID.
    :param db:
    :param product_id:
    :return:
    """

    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
    stmt = select(Category).where(Category.id == db_product.category_id, Category.is_active == True)
    result_cat = await db.scalars(stmt)
    db_category = result_cat.first()
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category not found")
    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(is_active=False)
    )
    await db.commit()
    await db.refresh(db_product)
    return {"status": "success", "message": "Product marked as inactive"}
