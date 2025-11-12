import logging
from typing import List

from fastapi import APIRouter, HTTPException
from starlette.responses import Response
from starlette.requests import Request

from src.model.agent import AgentsSystem
from src.business.verify import verify
from src.core.constants import KEY_SELECTED_AGENT_SYSTEMS, KEY_SESSION_ID, KEY_PASSWORD_SALT, ONE_DAY_IN_SECONDS
from src.model.agent import AgentsSystemListResponse, AgentsSystemRequest
from src.model.common import StandardResponse

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get(
    path="/v1/agent_systems",
    response_model=AgentsSystemListResponse,
    summary="Получить список всех систем агентов"
)
async def get_agent_systems(
        response: Response,
        request: Request
) -> AgentsSystemListResponse:
    await verify(request=request)

    systems: List[AgentsSystem] = [s for s in AgentsSystem]
    logger.info(f"Отправка списка агентных систем: {[s.value for s in systems]}")
    return AgentsSystemListResponse(systems=systems)


@router.put(
    path="/v1/set_agent_system",
    response_model=StandardResponse,
    summary="Устанавливаем выбранную систему агента"
)
async def set_agent_system(
        value: AgentsSystemRequest,
        response: Response,
        request: Request
) -> StandardResponse:
    await verify(request=request)

    logger.info(f"сохраняем в куки {KEY_SELECTED_AGENT_SYSTEMS}={value.system}")
    response.set_cookie(
        key=KEY_SELECTED_AGENT_SYSTEMS,
        value=value.system.value,
        httponly=True,
        max_age=ONE_DAY_IN_SECONDS,
    )
    return StandardResponse(
        message=f"Система {value.system} выбрана",
        success=True,
    )
