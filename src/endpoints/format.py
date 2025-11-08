import logging
from typing import List
from starlette.responses import Response
from starlette.requests import Request

from fastapi import APIRouter

from src.business.verify import verify
from src.core.constants import KEY_SESSION_ID, KEY_PASSWORD_SALT, KEY_SELECTED_FORMAT_TYPE_REQUEST, ONE_DAY_IN_SECONDS, \
    KEY_SELECTED_FORMAT_REQUEST
from src.model.common import StandardResponse
from src.model.format import FormatTypeRequest, FormatTypeListResponse
from src.model.tape_formats_response import FormatType

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    path="/v1/response_formats",
    response_model=FormatTypeListResponse,
    summary="Получить список всех способов ответа"
)
async def get_response_formats(
        response: Response,
        request: Request
) -> FormatTypeListResponse:
    await verify(request=request)

    formats: List[FormatType] = [s for s in FormatType]
    logger.info(f"Отправка списка способов ответа: {[s.value for s in formats]}")
    return FormatTypeListResponse(formats=formats)


@router.put(
    path="/v1/set_response_format",
    response_model=StandardResponse,
    summary="Сохранить способ ответа")
async def set_response_format(
        value: FormatTypeRequest,
        response: Response,
        request: Request
) -> StandardResponse:
    await verify(request=request)

    logger.info(f"сохраняем в куки {KEY_SELECTED_FORMAT_TYPE_REQUEST}={value.format}")
    response.set_cookie(
        key=KEY_SELECTED_FORMAT_TYPE_REQUEST,
        value=value.format_type,
        httponly=True,
        max_age=ONE_DAY_IN_SECONDS,
    )

    response.set_cookie(
        key=KEY_SELECTED_FORMAT_REQUEST,
        value=value.format,
        httponly=True,
        max_age=ONE_DAY_IN_SECONDS,
    )

    return StandardResponse(
        message=f"Система {value.format} выбрана",
        success=True,
    )
