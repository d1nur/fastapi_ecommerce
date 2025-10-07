from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, description="Пароль (минимум 8 символов)")
    role: str = Field(default="buyer", pattern="^(buyer|seller)$", description="Роль: 'buyer' или 'seller'")


class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории
    """
    name: str = Field(min_length=3, max_length=50, description="Название категории (3-50 символов)")
    parent_id: int | None = Field(description="ID родительской категории, если есть")


class Category(BaseModel):
    """
    Модель для ответа с данными категории.
    """
    id: int = Field(description="Уникальный идентификатор категории")
    name: str = Field(description="Название категории")
    parent_id: int | None = Field(default=None, description="ID родительской категории, если есть")
    is_active: bool = Field(description="Активность категории")

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    """
    name: str = Field(min_length=3, max_length=100, description="Название товара (3-100 символов)")
    description: str | None = Field(max_length=500, description="Описание товара (до 500 символов)")
    price: float = Field(gt=0, description="Цена товара (больше 0)")
    image_url: str | None = Field(max_length=200, description="URL изображения товара")
    stock: int = Field(ge=0, description="Количество товара на складе (0 или больше)")
    category_id: int = Field(description="ID категории, к которой относится товар")


class Product(BaseModel):
    """
    Модель для ответа с данными товара
    """
    id: int = Field(description="Уникальный идентификатор товара")
    name: str = Field(description="Название товара")
    description: str | None = Field(description="Описание товара")
    price: float = Field(description="Цена товара")
    image_url: str | None = Field(description="URL изображения товара")
    stock: int = Field(description="Количество товара на складе")
    category_id: int = Field(description="ID категории")
    rating: float = Field(description="Рейтинг товара")
    is_active: bool = Field(description="Активность товара")

    model_config = ConfigDict(from_attributes=True)


class ReviewsCreate(BaseModel):
    product_id: int = Field(description="ID продукта")
    comment: str | None = Field(description="Текст отзыва")
    grade: int = Field(ge=1, le=5, description="Оценка")


class Reviews(BaseModel):
    id: int = Field(description="Уникальный идентификатор отзыва")
    user_id: int = Field(description="ID пользователя")
    product_id: int = Field(description="ID продукта")
    comment: str | None = Field(description="Текст отзыва")
    comment_date: datetime = Field(description="Дата и время отзыва")
    grade: int = Field(ge=1, le=5, description="Оценка")
    is_active: bool = Field(description="Активность отзыва")

    model_config = ConfigDict(from_attributes=True)
