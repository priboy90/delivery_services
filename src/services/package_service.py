# src/services/package_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from uuid import uuid4

from src.models.models import Packages, Users
from src.models.schemas import PackageCreate


async def create_package(db: AsyncSession, package_data: PackageCreate) -> dict:
    """
    Создает новую посылку и возвращает её данные
    """
    # Генерируем уникальный ID посылки
    unique_id = uuid4()

    # Проверка существования типа посылки
    # Если нужна дополнительная логика проверки типа, можно добавить здесь

    # Создаем объект посылки
    new_package = Packages(
        name=package_data.name,
        weight=package_data.weight,
        type_id=package_data.type_id,
        item_value=package_data.item_value,
        user_id=unique_id
    )

    db.add(new_package)
    await db.flush()  # Принудительно сохраняем, чтобы получить ID

    # Возвращаем минимальную информацию пользователю
    return {
        "id": new_package.id,
        "name": new_package.name,
        "weight": new_package.weight,
        "type_id": new_package.type_id,
        "item_value": new_package.item_value,
        "calculated_cost": new_package.calculated_cost,
    }