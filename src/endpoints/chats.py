import logging
from typing import List

from fastapi import APIRouter, HTTPException
from starlette.responses import Response
from starlette.requests import Request

<<<<<<< HEAD
from src.business.verify import verify
from src.business.messages_interactor import get_all_chats, get_all_messages_chat
from src.core.constants import KEY_SELECTED_CHAT, KEY_SESSION_ID, KEY_PASSWORD_SALT, ONE_DAY_IN_SECONDS
from src.model.messages import MessageList
=======
from src.model.agent import Agent
from src.business.verify import verify
from src.business.messages_interactor import get_all_chats, get_all_messages_chat
from src.core.constants import KEY_SELECTED_CHAT, KEY_SESSION_ID, KEY_PASSWORD_SALT, ONE_DAY_IN_SECONDS
>>>>>>> 3de0af0 (Разбивает базу на разные чаты)
from src.model.chat import ChatList, Chat, ChatIdRequest
from src.model.common import StandardResponse

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get(
    path="/v1/chats",
<<<<<<< HEAD
    response_model=ChatList,
=======
    response_model=AgentsSystemListResponse,
>>>>>>> 3de0af0 (Разбивает базу на разные чаты)
    summary="Получить список всех чатов"
)
async def get_chats(
        response: Response,
        request: Request
) -> ChatList:
    await verify(request=request)
    list_chats: ChatList = get_all_chats()
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
