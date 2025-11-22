import logging

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

from src.chat.core.configs import settings
from src.chat.core.constants import KEY_SELECTED_CHAT, KEY_SELECTED_FORMAT_TYPE_REQUEST, ONE_DAY_IN_SECONDS, \
    KEY_SESSION_ID, KEY_PASSWORD_SALT, CHATS_DEFAULT
from src.chat.model.tape_formats_response import FormatType

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    path="/",
    response_class=HTMLResponse
)
async def root() -> HTMLResponse:
    return HTMLResponse("""
        <html>
            <head>
                <meta http-equiv="refresh" content="0; url=/chat" />
            </head>
            <body>
                <p>Перенаправление на <a href="/chat">страницу чата</a>...</p>
            </body>
        </html>
    """)


@router.get(
    path="/chat",
    response_class=HTMLResponse
)
async def chat_page(
        request: Request
) -> HTMLResponse:
    id_chat = request.cookies.get(KEY_SELECTED_CHAT)
    format_response = request.cookies.get(KEY_SELECTED_FORMAT_TYPE_REQUEST)
    session_id = request.cookies.get(KEY_SESSION_ID)
    password_salt = request.cookies.get(KEY_PASSWORD_SALT)

    if not id_chat:
        id_chat = CHATS_DEFAULT[0].id

    if not format_response:
        format_response = FormatType.DEFAULT

    try:
        path_site: str = str(settings.SITE_DIR)
        logger.info(f"Попытка открыть {path_site}/index.html")
        with open(f"{path_site}/index.html", encoding="utf-8") as f:
            logger.info("📄 Страница чата загружена")
            response = HTMLResponse(f.read())

            if session_id:
                response.set_cookie(
                    key=KEY_SESSION_ID,
                    value=session_id,
                    httponly=True,
                    max_age=ONE_DAY_IN_SECONDS,
                )

            if password_salt:
                response.set_cookie(
                    key=KEY_PASSWORD_SALT,
                    value=password_salt,
                    httponly=True,
                    max_age=ONE_DAY_IN_SECONDS,
                )

            response.set_cookie(
                key=KEY_SELECTED_CHAT,
                value=id_chat,
                httponly=True,
                max_age=ONE_DAY_IN_SECONDS,
            )
            response.set_cookie(
                key=KEY_SELECTED_FORMAT_TYPE_REQUEST,
                value=format_response,
                httponly=True,
                max_age=ONE_DAY_IN_SECONDS,
            )
            return response
    except FileNotFoundError:
        logger.error("❌ Файл index.html не найден")
        return HTMLResponse(
            "<h1>404: Страница не найдена</h1><p>Файл index.html отсутствует</p>",
            status_code=404
        )
