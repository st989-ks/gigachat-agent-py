import logging
from typing import Optional

from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.responses import Response

from src.business.messages_interactor import process_message, delete_all_messages_chat, get_all_messages_chat
from src.business.verify import verify
from src.core.constants import KEY_SELECTED_FORMAT_TYPE_REQUEST, CHATS_DEFAULT, KEY_SELECTED_CHAT, KEY_SESSION_ID
from src.model.common import StandardResponse
from src.model.chat import ChatList, Chat
from src.model.messages import MessageRequest, Message, MessageList
from src.model.tape_formats_response import FormatType

router = APIRouter()

logger = logging.getLogger(__name__)


@router.put("/v1/message")
async def message(
        value: MessageRequest,
        response: Response,
        request: Request
) -> MessageList:
    await verify(request=request)
    id_chat: Optional[str] = request.cookies.get(KEY_SELECTED_CHAT)
    format_type_text: Optional[str] = request.cookies.get(KEY_SELECTED_FORMAT_TYPE_REQUEST)
    id_session: Optional[str] = request.cookies.get(KEY_SESSION_ID)

    if not id_session:
        id_session = ""

    if not id_chat:
        id_chat = CHATS_DEFAULT[0].id

    try:
        format_type: FormatType = FormatType(format_type_text)
    except ValueError:
        logger.error(f"Неверное значение FormatType {format_type_text}")
        format_type: FormatType = FormatType.DEFAULT

    return await process_message(
        session_id=id_session,
        format_type=format_type,
        id_chat=id_chat,
        value=value,
    )


@router.get("/v1/history_message")
async def get_history_message(
        id: str = Query(..., description="Chat ID"),
        response: Response = None,
        request: Request = None
) -> MessageList:
    await verify(request=request)
    return await get_all_messages_chat(id)


@router.delete("/v1/history_message")
async def delete_history_message(
        id: int = Query(..., description="Chat ID"),
        response: Response = None,
        request: Request = None
) -> StandardResponse:
    await verify(request=request)
    await delete_all_messages_chat(id_chat=id)
    return StandardResponse(
        message="История удалена",
        success=True
    )
