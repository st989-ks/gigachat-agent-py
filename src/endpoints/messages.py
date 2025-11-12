import logging
from typing import Optional

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from src.model.agent import AgentsSystem
from src.business.messages_interactor import process_message, delete_all_messages, get_all_messages
from src.business.verify import verify
from src.core.constants import KEY_SELECTED_FORMAT_TYPE_REQUEST, KEY_SELECTED_AGENT_SYSTEMS, KEY_SESSION_ID
from src.model.common import StandardResponse
from src.model.messages import MessageRequest, Message, MessageList
from src.model.tape_formats_response import FormatType

router = APIRouter()

logger = logging.getLogger(__name__)


@router.put("/v1/message")
async def message(
        value: MessageRequest,
        response: Response,
        request: Request
) -> Message:
    await verify(request=request)
    agent_system_type_text: Optional[str] = request.cookies.get(KEY_SELECTED_AGENT_SYSTEMS)
    format_type_text: Optional[str] = request.cookies.get(KEY_SELECTED_FORMAT_TYPE_REQUEST)
    session_id: Optional[str] = request.cookies.get(KEY_SESSION_ID)

    if not session_id:
        session_id = ""

    try:
        format_type: FormatType = FormatType(format_type_text)
    except ValueError:
        logger.error(f"Неверное значение FormatType {format_type_text}")
        format_type: FormatType = FormatType.DEFAULT

    try:
        agent_system_type: AgentsSystem = AgentsSystem(agent_system_type_text)
    except ValueError:
        logger.error(f"Неверное значение AgentsSystem {agent_system_type_text}")
        agent_system_type: AgentsSystem = AgentsSystem.DEFAULT

    return await process_message(
        session_id=session_id,
        format_type=format_type,
        agent_system_type=agent_system_type,
        value=value,
    )


@router.get("/v1/history_message")
async def get_history_message(
        response: Response,
        request: Request
) -> MessageList:
    await verify(request=request)
    return await get_all_messages()


@router.delete("/v1/history_message")
async def delete_history_message(
        response: Response,
        request: Request
) -> StandardResponse:
    await verify(request=request)
    await delete_all_messages()
    return StandardResponse(
        message="История удалена",
        success=True
    )
