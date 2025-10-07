from pydantic import BaseModel, validator, condecimal, constr
from typing import Optional, List
from decimal import Decimal
from uuid import UUID


# Входные данные для регистрации посылки
class PackageCreate(BaseModel):
    name: constr(min_length=1, max_length=100)
    weight: condecimal(gt=0, le=1000)  # > 0 и <= 1000
    type_id: int
    item_value: condecimal(ge=0, le=1000000)  # >= 0 и <= 1,000,000

    @validator('name')
    def name_cannot_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя посылки не может быть пустым')
        return v.strip()


# Ответ после регистрации посылки
class PackageResponse(BaseModel):
    id: int
    name: str
    weight: Decimal
    type_id: int
    item_value: Decimal
    calculated_cost: Optional[Decimal] = None

    class Config:
        from_attributes = True


# Типы посылок
class PackageTypeResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Для пагинации и фильтрации
class PackageFilter(BaseModel):
    type_id: Optional[int] = None
    has_calculated_cost: Optional[bool] = None
    page: int = 1
    page_size: int = 10

    @validator('page')
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Страница должна быть положительной')
        return v

    @validator('page_size')# тупой фильтр переписать чтоб проверял макс страницу
    def page_size_must_be_reasonable(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Размер страницы должен быть от 1 до 100.')
        return v


# Полная информация о посылке
class PackageDetailResponse(BaseModel):
    id: int
    name: str
    weight: Decimal
    type_name: str
    item_value: Decimal
    calculated_cost: Optional[Decimal] = None

    class Config:
        from_attributes = True