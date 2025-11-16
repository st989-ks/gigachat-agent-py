import logging
from typing import List

from fastapi import HTTPException
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage

from src.ai.managers.giga_chat_manager import get_giga_chat_manager
from src.business.standart_process import StandartProcess
from src.db.db_manager import get_db_manager
from src.model.agent import Agent
from src.core.constants import CHATS_DEFAULT
from src.model.chat import Chat
from src.model.chat_models import GigaChatModel, ModelProvideType
from src.model.messages import (
    Message,
    MessageRequest,
    MessageList,
    MessageType,
    MessageOutput,
)
from src.model.tape_formats_response import FormatType
from src.tools.time import get_time_now_h_m_s

logger = logging.getLogger(__name__)


async def process_message(
    session_id: str,
    format_type: FormatType,
    chat: Chat,
    value: MessageRequest,
) -> MessageList:
    logger.info(f"Работа в чате {chat}")
    if chat.id == CHATS_DEFAULT[0].id:
        messages: MessageList = await StandartProcess(
            session_id=session_id, value=value
        ).process()
    elif chat.id == CHATS_DEFAULT[1].id:
        messages = await StandartProcess(session_id=session_id, value=value).process()
    else:
        messages = await StandartProcess(session_id=session_id, value=value).process()
    return messages


async def delete_all_messages() -> None:
    await get_db_manager().clear_all_table_messages()


async def delete_all_messages_chat(chat: Chat) -> None:
    await get_db_manager().remove_chat(id_chat=chat.id)


async def get_all_messages() -> MessageList:
    list_message: List[Message] = await get_db_manager().get_messages()
    return MessageList(messages=list_message)
