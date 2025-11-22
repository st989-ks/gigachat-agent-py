import logging

from starlette.requests import Request
from fastapi import HTTPException

from src.chat.business.session_interactor import get_session_manager
from src.chat.core.constants import KEY_SESSION_ID, KEY_PASSWORD_SALT

logger = logging.getLogger(__name__)


async def verify(
        request: Request
) -> None:
    session_id = request.cookies.get(KEY_SESSION_ID)
    password_salt = request.cookies.get(KEY_PASSWORD_SALT)
    verify_session = await get_session_manager().verify_session(
        session_id=session_id,
        cookie_password_salt=password_salt
    )
    if not verify_session:
        logger.warning(f"❌ Неверный пароль или нет сессии {session_id}")
        raise HTTPException(
            status_code=401,
            detail="Неверный пароль или нет сессии"
        )
