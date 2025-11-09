import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

import gigachat.exceptions
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from src.core.constants import KEY_SESSION_ID, ONE_DAY_IN_SECONDS
from src.endpoints.login import router as router_login
from src.endpoints.root import router as router_root
from src.endpoints.agents import router as router_agents
from src.endpoints.format import router as router_format
from src.endpoints.messages import router as router_messages
from src.model.error import ErrorDetail, ErrorResponse
from src.ai.manager import setup_ai_manager
from src.core.configs import settings
from src.core.logging_config import setup_logging
from src.db.db_manager import get_db_manager

logger = logging.getLogger(__name__)


def get_application() -> FastAPI:
    setup_logging()
    setup_ai_manager(
        credentials=settings.AUTH_KEY,
        verify_ssl_certs=False
    )
    get_db_manager()
    logger.info("Starting chat...")
    fast_app = FastAPI(
        title="Агент AI",
        lifespan=_lifespan,
        debug=settings.debug,
        description="Веб-интерфейс для работы с GigaChat API",
        version=settings.version,
    )
    fast_app.add_middleware(SessionInitMiddleware)
    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fast_app.include_router(router_login)
    fast_app.include_router(router_root)
    fast_app.include_router(router_agents)
    fast_app.include_router(router_format)
    fast_app.include_router(router_messages)

    @fast_app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    message=str(exc.detail),
                    type="http",
                    code="HTTP_EXCEPTION",
                    param=None
                )
            ).model_dump(),
        )

    @fast_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    message=str(exc.errors()),
                    type="invalid_request_error",
                    code="BAD_REQUEST",
                    param=None
                )
            ).model_dump(),
        )

    @fast_app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    message=str(exc),
                    type="http",
                    code="HTTP_EXCEPTION",
                    param=None
                )
            ).model_dump(),
        )

    @fast_app.exception_handler(gigachat.exceptions.ResponseError)
    async def response_error_handler(request: Request, exc: gigachat.exceptions.ResponseError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    message=str(exc),
                    type="http",
                    code="HTTP_EXCEPTION",
                    param=None
                )
            ).model_dump(),
        )

    # ===== Подключение статических файлов =====
    path_site: str = str(settings.SITE_DIR)
    logger.info("🚀 Подключение статических файлов")
    fast_app.mount("/", StaticFiles(directory=path_site, html=True, check_dir=False), name="site")

    return fast_app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    logger.info("🚀 Приложение запускается...")
    print("\n" + "=" * 70)
    print("🚀 GigaChat Agent - Веб-сервер запущен")
    print("=" * 70)
    print("\n📍 Адреса доступа:")
    print("   - Веб-интерфейс: http://127.0.0.1:8010/chat")
    print("   - API документация: http://127.0.0.1:8010/docs")
    print("   - Альтернативная документация: http://127.0.0.1:8010/redoc")
    print("\n" + "=" * 70 + "\n")
    yield
    logger.info("🛑 Приложение выключается...")

class SessionInitMiddleware(BaseHTTPMiddleware):
    """Middleware для инициализации session_id в куки при первом запросе."""

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get(KEY_SESSION_ID)

        # Если session_id не существует, генерируем новый
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"🆔 Новый session_id создан: {session_id}")

        response = await call_next(request)

        # Устанавливаем session_id в куки если его нет или если это первый запрос
        if KEY_SESSION_ID not in request.cookies:
            response.set_cookie(
                key=KEY_SESSION_ID,
                value=session_id,
                httponly=True,
                max_age=ONE_DAY_IN_SECONDS,
            )
            logger.info(f"✅ session_id установлен в куки: {session_id}")

        return response

server = get_application()
