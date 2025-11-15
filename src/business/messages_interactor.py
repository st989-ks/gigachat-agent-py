import logging
from typing import List

from fastapi import HTTPException
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage, AIMessage

from src.ai.managers.giga_chat_manager import get_giga_chat_manager
from src.business.day_8 import ProcessDay8
from src.db.db_manager import get_db_manager
from src.model.agent import AgentsSystem, Agent
from src.model.chat_models import GigaChatModel, ModelProvideType
from src.model.messages import Message, MessageRequest, MessageList, MessageType, MessageOutput
from src.model.tape_formats_response import FormatType
from src.tools.time import get_time_now_h_m_s

logger = logging.getLogger(__name__)


async def process_message(
        session_id: str,
        format_type: FormatType,
        agent_system_type: AgentsSystem,
        value: MessageRequest,
) -> MessageList:
    logger.info(f"Запускаем тип {agent_system_type}")
    if agent_system_type == AgentsSystem.COMPARE_ANSWERS:
        messages: MessageList = await _process_compare_answers(
            session_id=session_id,
            value=value,
        )
    elif agent_system_type == AgentsSystem.TECHNICAL_SPECIFICATION:
        messages = await _process_technical_specification(
            session_id=session_id,
            format_type=format_type,
            value=value,
        )
    elif agent_system_type == AgentsSystem.DEFAULT:
        messages = await _process_default(
            session_id=session_id,
            value=value,
        )
    elif agent_system_type == AgentsSystem.SUMMARY_DIALOG:
        messages = await ProcessDay8(
            session_id=session_id,
            value=value,
        ).process()
    else:
        logger.warning(f"❌ Не реализован компонент {agent_system_type}")
        raise HTTPException(
            status_code=503,
            detail="Не реализован компонент {agent_system_type}"
        )
    return messages


async def delete_all_messages() -> None:
    await get_db_manager().clear_all_table_messages()


async def get_all_messages() -> MessageList:
    list_message: List[Message] = await get_db_manager().get_messages()
    return MessageList(messages=list_message)


async def _process_compare_answers(
        session_id: str,
        value: MessageRequest,
) -> MessageList:
    return await _process_default(
        session_id=session_id,
        value=value,
    )


async def _process_technical_specification(
        session_id: str,
        format_type: FormatType,
        value: MessageRequest,
) -> MessageList:
    return await _process_default(
        session_id=session_id,
        value=value,
    )


async def _process_default(
        session_id: str,
        value: MessageRequest,
) -> MessageList:
    try:
        message: Message = Message(
            id=None,
            session_id=session_id,
            message_type=MessageType.USER,
            agent_id=None,
            name="User",
            timestamp=get_time_now_h_m_s(),
            message=value.message,
            prompt_tokens=0,
            completion_tokens=0,
            request_time=0,
            price=0,
            meta="",
        )
        await get_db_manager().add_message(message)
    except Exception as e:
        logger.error(f"Ошибка добавления сообщения: {e}")
        raise HTTPException(
            status_code=503,
            detail="Ошибка сохранения"
        )

    list_message: List[Message] = await get_db_manager().get_messages()

    agent: Agent = Agent(
        agent_id="Agent",
        name="Вассерман Анатолий",
        provider=ModelProvideType.GIGA_CHAT.value,
        temperature=0,
        model="GigaChat-2",
        max_tokens=None,
    )

    agent_id = agent.agent_id
    name = agent.name

    messages: List[BaseMessage] = []

    for msg in list_message:
        message_type = msg.message_type
        content = msg.message

        if message_type == MessageType.AI:
            messages.append(AIMessage(content=content))
        elif message_type == MessageType.USER:
            messages.append(HumanMessage(content=content))
        elif message_type == MessageType.SYSTEM:
            logger.info(f"MessageType.SYSTEM content='''{content}'''")

    message_from_model: MessageOutput = get_giga_chat_manager().invoke(
        agent=agent,
        input_messages=messages,
        config=None,
        stop=None,
    )

    if isinstance(message_from_model.message.content, str):
        content = message_from_model.message.content
    else:
        content = str(message_from_model.message.content)

    message = Message(
        id=None,
        session_id=session_id,
        agent_id=agent_id,
        message_type=MessageType.AI,
        name=name,
        timestamp=get_time_now_h_m_s(),
        message=content,
        prompt_tokens=message_from_model.prompt_tokens,
        completion_tokens=message_from_model.completion_tokens,
        request_time=message_from_model.request_time,
        price=message_from_model.price,
        meta=message_from_model.meta,
    )

    try:
        db_message = await get_db_manager().add_message(message)
        if not db_message:
            raise
        message = db_message

    except Exception as e:
        logger.error(f"Ошибка добавления сообщения: {e}")
        raise HTTPException(
            status_code=503,
            detail="Ошибка сохранения сообщения в чате"
        )

    return MessageList(messages=[message])
