from itsdangerous import URLSafeSerializer
from starlette.middleware.sessions import SessionMiddleware
import uuid
from fastapi import Request
from .settings import settings

# Секретный ключ для подписи сессий (в продакшене хранить в env переменных)
SECRET_KEY = settings.SECRET_KEY
SESSION_COOKIE_NAME = settings.SESSION_COOKIE_NAME

# Инициализация сериализатора для подписи сессий
serializer = URLSafeSerializer(SECRET_KEY)


def get_session_config():
    """Возвращает конфигурацию для SessionMiddleware"""
    return {
        "secret_key": SECRET_KEY,
        "session_cookie": SESSION_COOKIE_NAME,
        "max_age": 14 * 24 * 60 * 60,  # 14 дней
        "same_site": "lax",
        "https_only": False  # Для разработки
    }


def create_session_id() -> str:
    """Создание уникального ID сессии"""
    return str(uuid.uuid4())


def get_session_id(request: Request) -> str:
    """Получение session_id из запроса"""
    return request.session.get("session_id")


def set_session_id(request: Request, session_id: str) -> None:
    """Установка session_id в сессию"""
    request.session["session_id"] = session_id


def ensure_session_id(request: Request) -> str:
    """Гарантирует наличие session_id в сессии, создает если нет"""
    session_id = get_session_id(request)
    if not session_id:
        session_id = create_session_id()
        set_session_id(request, session_id)
    return session_id
