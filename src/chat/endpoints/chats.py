import logging
from typing import List

from fastapi import APIRouter, HTTPException
from starlette.responses import Response
from starlette.requests import Request

from src.chat.business.verify import verify
from src.chat.business.messages_interactor import get_all_chats, get_all_messages_chat
from src.chat.core.constants import KEY_SELECTED_CHAT, ONE_DAY_IN_SECONDS
from src.chat.model.messages import MessageList
from src.chat.model.chat import ChatList, ChatIdRequest

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get(
    path="/v1/chats",
    response_model=ChatList,
    summary="Получить список всех чатов"
)
async def get_chats(
        response: Response,
        request: Request
) -> ChatList:
    await verify(request=request)
    # Ждём выполнение корутины и получаем результат
    list_chats: ChatList = await get_all_chats()
    logger.info(f"Отправка списка чатов: {list_chats}")
    return list_chats

@router.put(
    path="/v1/set_chat",
    response_model=MessageList,
    summary="Устанавливаем выбранный чат в куки и возвращяем список чата"
)
async def set_chat(
        value: ChatIdRequest,
        response: Response,
        request: Request
) -> MessageList:
    await verify(request=request)

    logger.info(f"сохраняем в куки {KEY_SELECTED_CHAT}={value.id}")
    response.set_cookie(
        key=KEY_SELECTED_CHAT,
        value=value.id,
        httponly=True,
        max_age=ONE_DAY_IN_SECONDS,
    )
    return await get_all_messages_chat(value.id)