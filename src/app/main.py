# FILE: src/app/main.py
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import select

from .api.analytics import router as analytics_router
from .api.parcels import router as parcels_router
from .api.responses import err, ok
from .api.types import router as types_router
from .config import get_settings
from .db.postgres import get_engine, session_scope
from .logging import setup_logging
from .middleware.session import SessionMiddleware
from .models.parcel_type import ParcelType
from .services.mongo import Mongo

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["now"] = datetime.utcnow


async def _seed_parcel_types() -> None:
    """
    Идемпотентный сидер типов посылок.
    Требования ТЗ: 3 предзаданных типа (id: 1..3).
    Безопасен при повторных запусках; не роняет приложение при конфликте.
    """
    required = [
        (1, "одежда"),
        (2, "электроника"),
        (3, "разное"),
    ]
    async with session_scope() as session:
        existing = set(await session.scalars(select(ParcelType.name)))
        created = False
        for pid, name in required:
            if name not in existing:
                session.add(ParcelType(id=pid, name=name))
                created = True
        if created:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения:
    - проверка соединения с Postgres
    - инициализация Redis
    - опциональная инициализация Mongo
    - безопасный сид типов
    - корректное закрытие ресурсов
    """
    s = get_settings()
    setup_logging()

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(lambda *_: None)

    app.state.redis = redis_from_url(s.redis_url, decode_responses=True)

    mongo: Mongo | None = None
    if s.mongodb_url:
        mongo = Mongo(s.mongodb_url, db_name="delivery")
        await mongo.connect()
    app.state.mongo = mongo

    try:
        await _seed_parcel_types()
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning("Seeding parcel types skipped: %s", e)

    try:
        yield
    finally:
        redis = getattr(app.state, "redis", None)
        if redis is not None:
            try:
                await redis.aclose()
            except Exception:
                pass
        if mongo is not None:
            try:
                await mongo.close()
            except Exception:
                pass


def create_app() -> FastAPI:
    """
    Фабрика приложения FastAPI.
    Важно: роутеры подключаются под префиксом из настроек (по ТЗ — /api/v1).
    """
    s = get_settings()
    app = FastAPI(
        title=s.project_name,
        version=s.app_version,
        docs_url=s.docs_url,
        redoc_url=s.redoc_url,
        lifespan=lifespan,
    )

    app.add_middleware(SessionMiddleware)

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/favicon.ico")
    async def favicon() -> FileResponse:
        return FileResponse(static_dir / "favicon.ico")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> ORJSONResponse:
        def to_primitive(v):
            if isinstance(v, Decimal):
                return float(v)
            if isinstance(v, dict):
                return {k: to_primitive(x) for k, x in v.items()}
            if isinstance(v, list | tuple):
                return [to_primitive(x) for x in v]
            return v

        cleaned_errors = to_primitive(exc.errors())
        payload = err("validation_error", "Validation failed", {"errors": cleaned_errors})
        payload["code"] = "validation_error"
        return ORJSONResponse(status_code=422, content=payload)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return JSONResponse(status_code=exc.status_code, content=err("http_error", message))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content=err("internal_error", str(exc)))

    api_prefix = s.api_v1_prefix
    app.include_router(types_router, prefix=api_prefix, tags=["types"])
    app.include_router(parcels_router, prefix=api_prefix, tags=["parcels"])
    app.include_router(analytics_router, prefix=api_prefix, tags=["analytics"])

    # Healthcheck
    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse(ok(True))

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("home.html", {"request": request})

    @app.get("/parcels", response_class=HTMLResponse)
    async def parcels_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("parcels.html", {"request": request})

    return app


app = create_app()
