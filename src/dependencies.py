from fastapi import Request, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from .core.database import get_db
from .core.session import ensure_session_id, get_session_id
from .models.models import Users


async def get_current_user(
        request: Request,
        response: Response,
        db: Session = Depends(get_db)
) -> Users:
    """
    Dependency для получения текущего пользователя по session_id
    Создает нового пользователя если сессия новая
    """
    session_id = ensure_session_id(request)

    # Проверяем, есть ли у пользователя cookie с session_id
    if not request.cookies.get("session_id"):
        # Если нет cookie, устанавливаем его
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=14 * 24 * 60 * 60,  # 14 дней
            httponly=True,
            samesite="lax"
        )

    # Ищем пользователя по session_id
    result = await db.execute(select(Users).filter(Users.session_id == session_id))
    user = result.scalar_one_or_none()

    if not user:
        # Создаем нового пользователя для этой сессии
        user = Users(
            session_id=session_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Обновляем время последней активности
        user.last_activity = datetime.utcnow()
        await db.commit()

    return user


async def get_optional_user(request: Request, db: Session = Depends(get_db)):
    """
    Optional dependency - возвращает пользователя если есть, иначе None
    """
    session_id = get_session_id(request)
    if not session_id:
        return None

    result = await db.execute(select(Users).filter(Users.session_id == session_id))
    user = result.scalar_one_or_none()

    if user:
        user.last_activity = datetime.utcnow()
        await db.commit()

    return user
