from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy.orm import relationship, validates
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Uuid, DECIMAL, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)
    session_id = Column(String, unique=True, index=True)

    packages = relationship("Packages", back_populates="user")

    @validates('last_activity')
    def validate_last_activity(self, key, value):
        if value and value > datetime.utcnow():
            raise ValueError("Последнее действие не может быть в будущем.")
        return value


class Types(Base):
    __tablename__ = "types"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    packages = relationship("Packages", back_populates="type")

    @validates('name')
    def validate_name(self, key, name):
        if not name or len(name.strip()) == 0:
            raise ValueError("Имя типа не может быть пустым")
        if len(name) > 50:
            raise ValueError("Слишком длинное имя")
        return name.strip()


class Packages(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Uuid, ForeignKey('users.id'), nullable=False, index=True)
    type_id = Column(Integer, ForeignKey('types.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    weight = Column(DECIMAL(10, 2))
    item_value = Column(DECIMAL(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    calculated_cost = Column(DECIMAL(10, 2))

    user = relationship("Users", back_populates="packages")
    type = relationship("Types", back_populates="packages")

    # Проверки на уровне БД
    __table_args__ = (
        CheckConstraint('weight > 0', name='check_positive_weight'),
        CheckConstraint('item_value >= 0', name='check_non_negative_value'),
        CheckConstraint('calculated_cost >= 0 OR calculated_cost IS NULL', name='check_non_negative_cost'),
    )

    @validates('name')
    def validate_name(self, key, name):
        if not name or len(name.strip()) == 0:
            raise ValueError("Имя посылки не может быть пустым")
        if len(name) > 100:
            raise ValueError("Слишком длинное имя посылки")
        return name.strip()

    @validates('weight')
    def validate_weight(self, key, weight):
        if weight is None:
            raise ValueError("Требуется вес!")
        weight_decimal = Decimal(str(weight))
        if weight_decimal <= 0:
            raise ValueError("Вес должен быть положительным")
        if weight_decimal > Decimal('1000'):  # Макс 1000 кг
            raise ValueError("Слишком большой вес")
        return weight_decimal

    @validates('item_value')
    def validate_item_value(self, key, value):
        if value is None:
            raise ValueError("Укажите цену посылки")
        value_decimal = Decimal(str(value))
        if value_decimal < 0:
            raise ValueError("Цена не может быть отрицательной.")
        if value_decimal > Decimal('1000000'):  # Макс 1 млн долларов
            raise ValueError("Нее друг воспользуйся инкасацией")
        return value_decimal

    @validates('calculated_cost')
    def validate_calculated_cost(self, key, cost):
        if cost is not None:
            cost_decimal = Decimal(str(cost))
            if cost_decimal < 0:
                raise ValueError("Рассчитанная стоимость не может быть отрицательной")
            if cost_decimal > Decimal('500000'):  # Макс 500k за доставку
                raise ValueError("Рассчитанная стоимость слишком высока")
        return cost
