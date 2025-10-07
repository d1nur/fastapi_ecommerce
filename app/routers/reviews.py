from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, update

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db

from app.models.reviews import Reviews as ReviewsModel
from app.models.products import Product
from app.schemas import Reviews as ReviewsSchema, ReviewsCreate
from app.models.users import User as UserModel
from app.auth import get_current_buyer, get_current_user

from sqlalchemy.sql import func


async def update_product_rating(db: AsyncSession, product_id: int):
    """
    Пересчет рейтинга товара
    :param db:
    :param product_id:
    :return:
    """
    result = await db.execute(
        select(func.avg(ReviewsModel.grade)).where(
            ReviewsModel.product_id == product_id,
            ReviewsModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(Product, product_id)
    product.rating = round(avg_rating, 2)
    await db.commit()


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


@router.get("/", response_model=list[ReviewsSchema], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает все отзывы
    :param db:
    :return:
    """
    stmt = select(ReviewsModel).where(ReviewsModel.is_active == True)
    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews


@router.get("/products/{product_id}/reviews/", response_model=list[ReviewsSchema], status_code=status.HTTP_200_OK)
async def get_reviews_by_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает отзывы к определенному товару
    :param product_id:
    :param db:
    :return:
    """
    stmt = select(Product).where(Product.id == product_id, Product.is_active == True)
    result = await db.scalars(stmt)
    if result.first() is None:
        raise HTTPException(status_code=404, detail="Product not found")
    stmt = select(ReviewsModel).where(ReviewsModel.product_id == product_id, ReviewsModel.is_active == True)
    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews


@router.post("/", response_model=ReviewsSchema, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewsCreate,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_buyer)):
    """
    Создание нового отзыва
    :param review:
    :param db:
    :param current_user:
    :return:
    """
    stmt = select(Product).where(Product.id == review.product_id,
                                 Product.is_active == True)
    result = await db.scalars(stmt)
    product = result.first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    stmt = select(ReviewsModel).where(ReviewsModel.product_id == product.id, ReviewsModel.user_id == current_user.id, ReviewsModel.is_active == True)
    result = await db.scalars(stmt)
    review_res = result.first()
    if review_res:
        raise HTTPException(status_code=409, detail="You already have a review for this product")
    if review.grade < 0 or review.grade > 5:
        raise HTTPException(status_code=422, detail="Grade should be in range 0-5")

    db_review = ReviewsModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    await update_product_rating(db, product.id)
    return db_review


@router.delete("/{reviews_id}", status_code=status.HTTP_200_OK)
async def delete_review(reviews_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    """
    Мягкое удаление отзыва по его ID. Только для роли admin
    :param reviews_id:
    :param db:
    :param current_user:
    :return:
    """
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only admin can do this")
    stmt = select(ReviewsModel).where(ReviewsModel.id == reviews_id, ReviewsModel.is_active == True)
    result = await db.scalars(stmt)
    review = result.first()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.execute(
        update(ReviewsModel)
        .where(ReviewsModel.id == reviews_id)
        .values(is_active=False)
    )
    await db.commit()
    await db.refresh(review)
    await update_product_rating(db, review.product_id)
    return {"message": "Review deleted"}


