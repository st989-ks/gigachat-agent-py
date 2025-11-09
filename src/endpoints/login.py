import logging

from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from src.business.session_interactor import get_session_manager
from src.core.constants import KEY_PASSWORD_SALT, KEY_SESSION_ID, ONE_DAY_IN_SECONDS
from src.model.common import StandardResponse
from src.model.verify import AuthResponse

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    path="/v1/login",
    response_model=StandardResponse,
    summary="Вход по паролю"
)
async def login_endpoint(
        value: AuthResponse,
        response: Response,
        request: Request
) -> StandardResponse:
    session_id = request.cookies.get(KEY_SESSION_ID)

    salt = await get_session_manager().login(
        session_id=session_id,
        password=value.password
    )

    if not salt:
        logger.warning(f"❌ Неверный пароль для сессии {session_id}")
        raise HTTPException(
            status_code=401,
            detail="Неверный пароль"
        )

    logger.info(f"сохраняем в куки {KEY_PASSWORD_SALT}={salt}, {KEY_SESSION_ID}={session_id}")

    response.set_cookie(
        key=KEY_PASSWORD_SALT,
        value=salt,
        httponly=True,
        max_age=ONE_DAY_IN_SECONDS,
    )

    response.set_cookie(
        key=KEY_SESSION_ID,
        value=session_id,
        httponly=True,
        max_age=ONE_DAY_IN_SECONDS,
    )

    return StandardResponse(message=salt)

@router.get(
    path="/v1/check-auth",
    response_model=StandardResponse,
    summary="Проверить авторизацию"
)
async def check_auth(
        response: Response,
        request: Request
) -> StandardResponse:
    session_id = request.cookies.get(KEY_SESSION_ID)
    password_salt = request.cookies.get(KEY_PASSWORD_SALT)

    if not session_id or not password_salt:
        raise HTTPException(
            status_code=401,
            detail="Не авторизован"
        )

    # Проверяем валидность
    result = await get_session_manager().verify_session(
        session_id=session_id,
        cookie_password_salt=password_salt
    )

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Невалидная сессия"
        )

    return StandardResponse(
        message="Авторизован",
        success=True
    )
