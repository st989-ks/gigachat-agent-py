import logging
from typing import List

from src.business.standart_process import StandartProcess
from src.db.db_manager import get_db_manager
from src.core.constants import CHATS_DEFAULT
from src.model.chat import Chat, ChatList
from src.business.mcp_processor import McpProcessor
from src.business.telegram_scanner import stop_scanner_service, start_scanner_service, get_scanner_service
from src.tools.time import get_time_now_h_m_s
from src.model.messages import (
    Message,
    MessageRequest,
    MessageList,
    MessageType
)
from src.model.tape_formats_response import FormatType

logger = logging.getLogger(__name__)


async def process_message(
    session_id: str,
    format_type: FormatType,
    chat_id: str,
    value: MessageRequest,
) -> MessageList:
    chat: Chat = await get_db_manager().get_chat_by_id(chat_id) # type: ignore
    logger.info(f"Работа в чате {chat_id}")
    if chat_id == CHATS_DEFAULT[0].id:
        messages: MessageList = await StandartProcess(
            session_id=session_id, chat=chat, value=value
        ).process()
    elif chat_id == CHATS_DEFAULT[1].id:
        messages = await StandartProcess(
            session_id=session_id, chat=chat, value=value
        ).process()
    elif chat_id == CHATS_DEFAULT[2].id:
        messages = await McpProcessor(
            session_id=session_id, chat=chat, value=value
        ).process()
    elif chat_id == CHATS_DEFAULT[3].id:
        if value.message == "/start":
            await start_scanner_service()
            response_text = "start_scanner_service"
        elif value.message == "/stop":
            await stop_scanner_service()
            response_text = "stop_scanner_service"
        elif value.message == "/status":
            service = get_scanner_service()
            is_running = service.analyzer.scheduler and service.analyzer.scheduler.running
            status = "🟢 РАБОТАЕТ" if is_running else "🔴 ОСТАНОВЛЕН"
            response_text = f"Статус сканера: {status}"
        else:
            response_text = "error command only  /start /stop /status"
        message =  Message(
                id=None,
                chat_id=chat_id,
                session_id=session_id,
                agent_id=None,
                message_type=MessageType.SYSTEM,
                name="system",
                timestamp= get_time_now_h_m_s(),
                message=response_text,
                prompt_tokens=0,
                completion_tokens=0,
                request_time=0,
                price=0,
                meta="----",
            )
        messages = MessageList(messages=[message])
    else:
        messages = await StandartProcess(
            session_id=session_id, chat=chat, value=value
        ).process()
    return messages


async def delete_all_messages() -> None:
    await get_db_manager().clear_all_table_messages()


async def delete_all_messages_chat(chat_id: str) -> None:
    await get_db_manager().remove_all_messages_chat(chat_id=chat_id)


async def get_all_messages() -> MessageList:
    chats = await get_db_manager().get_chats()
    list_message: List[Message] = []
    for chat in chats:
        list_message.extend(await get_db_manager().get_messages(chat_id=chat.id))

    return MessageList(messages=list_message)

async def get_all_messages_chat(chat_id: str) -> MessageList:
    list_message: List[Message] = await get_db_manager().get_messages(chat_id=chat_id)
    return MessageList(messages=list_message)

async def get_all_chats() -> ChatList:
    list_chats: list[Chat] = await get_db_manager().get_chats()
    return ChatList(chats=list_chats)
