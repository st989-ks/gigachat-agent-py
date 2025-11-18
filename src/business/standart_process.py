import logging
import asyncio
from typing import (
    List, 
    Final,
    Optional
)

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage

from src.ai.managers.giga_chat_manager import get_giga_chat_manager
from src.db.db_manager import get_db_manager
from src.model.chat import Chat
from src.model.agent import Agent
from src.model.chat_models import GigaChatModel, ModelProvideType
from src.model.messages import (
    Message,
    MessageRequest,
    MessageType,
    MessageList,
    MessageOutput,
)
from src.tools.time import get_time_now_h_m_s

logger = logging.getLogger(__name__)


class StandartProcess:

    THRESHOLD_MESSAGES: Final[int] = 10

    default_system_prompt: str = (
        "Ты  хороший друг и собеседник. Роль:\n"
        "1) Отвечать на вопросы, с размышлением.\n"
        "2) Будь дружелюбным, точным, информативным, и лаконичный, допускается дружественная дерзость\n"
    )

    default_agent_main: Agent = Agent(
        agent_id="Agent",
        name="Вассерман Анатолий",
        provider=ModelProvideType.GIGA_CHAT.value,
        temperature=0.6,
        model=GigaChatModel.STANDARD.value,
        max_tokens=800,
    )

    def __init__(
        self,
        session_id: str,
        chat: Chat,
        value: MessageRequest,
    ):
        self.chat: Chat = chat
        self.message_user: Message = Message(
            id=None,
            chat_id=chat.id,
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
            meta=""
        )

    async def process(self) -> MessageList:
        list_message: List[Message] = await get_db_manager().get_messages(
            chat_id=self.message_user.chat_id
        )

        logger.info(f"process list_message_len={len(list_message)}")
        if len(list_message) >= self.THRESHOLD_MESSAGES:
            response = await self._summary(list_message)
        else:
            response = await self._process_default(list_message)

        return MessageList(messages=response)

    @staticmethod
    def format_message(msg: Message) -> str:
        return f"[{msg.timestamp}] {msg.name} ({msg.message_type}): {msg.message}\n"

    async def _summary(self, list_message: list[Message]) -> List[Message]:
        messages_text = "\n\n".join([self.format_message(m) for m in list_message])

        summary_agent: Agent = Agent(
            agent_id="Agent",
            name="Суммиризатор",
            provider=ModelProvideType.GIGA_CHAT.value,
            temperature=0,
            model=GigaChatModel.MAX.value,
            max_tokens=None,
        )

        system_sammary_prompt: str = (
            f"Суммаризируй следующие сообщения кратко и точно.\n"
            f"Выведи только ключевые моменты без введений, пояснений и дополнительной информации.\n\n"
            f"{messages_text}\n\n"
            f"ВЫВОД: только суммаризация, никаких предисловий.\n```\n\n\n---\n"
        )

        summary_message_from_model: MessageOutput = get_giga_chat_manager().invoke(
            agent=summary_agent,
            input_messages=system_sammary_prompt,
            config=None,
            stop=None,
        )

        summary_message: Message = Message(
            id=None,
            chat_id=self.message_user.chat_id,
            session_id=self.message_user.session_id,
            message_type=MessageType.AI,
            agent_id="Agent",
            name="Суммиризатор",
            timestamp=get_time_now_h_m_s(),
            message=(
                f"СУММАРИЗАЦИЯ ПРЕДЫДУЩЕГО ДИАЛОГА:\n"
                f"{str(summary_message_from_model.message.content)}\n"
                f"{'-' * 10}"
            ),
            prompt_tokens=summary_message_from_model.prompt_tokens,
            completion_tokens=summary_message_from_model.completion_tokens,
            request_time=summary_message_from_model.request_time,
            price=summary_message_from_model.price,
            meta=summary_message_from_model.meta,
        )

        new_prompt_agent: Agent = Agent(
            agent_id="Agent",
            name="Промпт Инженер",
            provider=ModelProvideType.GIGA_CHAT.value,
            temperature=0,
            model=GigaChatModel.MAX.value,
            max_tokens=None,
        )

        system_optimizations_prompt: str = (
            f"Ты — движок оптимизации промптов для AI-агентов. На основе предыдущей суммаризации списка сообщений тебе нужно:\n\n"
            f"- Проанализировать полученную сводку ключевых моментов.\n"
            f"- Выявить пробелы, избыточности или места, требующие уточнений в исходном промпте.\n"
            f"- Внести улучшения в формулировках промпта, чтобы повысить релевантность и эффективность работы агента.\n"
            f"- Исправить тон, стиль и структуру запроса соглассно суммаризации.\n"
            f"- Выделить разделы промпта, которые можно упростить или наоборот дополнить.\n\n"
            f" СТАРЫЙ ПРОМПТ: \n\n{self.chat.system_prompt or self.default_system_prompt}\n\n"
            f" СУММАРИЗАЦИЯ: \n\n{str(summary_message_from_model.message.content)}\n\n"
            f"ВЫВОД: ТОЛЬКО ПРОМПТ, никаких предисловий.\n```\n\n\n---\n"
        )

        new_prompt_response: MessageOutput = get_giga_chat_manager().invoke(
            agent=new_prompt_agent,
            input_messages=system_optimizations_prompt,
            config=None,
            stop=None,
        )

        self.system_prompt = str(new_prompt_response.message.content)

        logger.info(f"New - system_prompt\n{self.system_prompt}\n")

        list_messages: List[BaseMessage] = [
            SystemMessage(self.system_prompt),
            AIMessage(summary_message.message),
            HumanMessage(self.message_user.message),
        ]

        response_from_model: MessageOutput = get_giga_chat_manager().invoke(
            agent=self.default_agent_main,
            input_messages=list_messages,
            config=None,
            stop=None,
        )

        response_message = Message(
            id=None,
            chat_id=self.message_user.chat_id,
            session_id=self.message_user.session_id,
            agent_id=self.default_agent_main.agent_id,
            message_type=MessageType.AI,
            name=self.default_agent_main.name,
            timestamp=get_time_now_h_m_s(),
            message=str(response_from_model.message.content),
            prompt_tokens=response_from_model.prompt_tokens,
            completion_tokens=response_from_model.completion_tokens,
            request_time=response_from_model.request_time,
            price=response_from_model.price,
            meta=(
                f"{response_from_model.meta}\n"
                "Новый промпт:\n"
                f"{self.system_prompt}"
            ),
        )

        await get_db_manager().remove_all_messages_chat(chat_id=self.message_user.chat_id)
        update_chat: Optional[Chat] =await get_db_manager().update_chat_system_prompt(
            chat_id = self.chat.id,
            system_prompt=self.system_prompt
        )

        if update_chat:
            self.chat = update_chat

        try:
            summary_message_db: Message = await get_db_manager().add_message(summary_message)  # type: ignore
            message_user_db: Message = await get_db_manager().add_message(self.message_user)  # type: ignore
            message_db: Message = await get_db_manager().add_message(response_message)  # type: ignore
        except Exception as e:
            print(f"❌ Ошибка добавления сообщений на уровне процесса суммаризации: {e}")
            raise HTTPException(status_code=503, detail="Ошибка сохранения")

        return [
            summary_message_db,
            message_user_db,
            message_db,
        ]

    async def _process_default(self, list_message: list[Message]) -> List[Message]:
        try:
            await get_db_manager().add_message(self.message_user)
        except Exception as e:
            logger.error(f"Ошибка добавления сообщения: {e}")
            raise HTTPException(status_code=503, detail="Ошибка сохранения")

        messages: List[BaseMessage] = [SystemMessage(self.chat.system_prompt or self.default_system_prompt)]

        for msg in list_message:
            message_type = msg.message_type
            content = msg.message

            if message_type == MessageType.AI:
                messages.append(AIMessage(content=content))
            elif message_type == MessageType.USER:
                messages.append(HumanMessage(content=content))
            elif message_type == MessageType.SYSTEM:
                logger.info(f"MessageType.SYSTEM content='''{content}'''")

        messages.append(HumanMessage(content=self.message_user.message))

        message_from_model: MessageOutput = get_giga_chat_manager().invoke(
            agent=self.default_agent_main,
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
            chat_id=self.message_user.chat_id,
            session_id=self.message_user.session_id,
            agent_id=self.default_agent_main.agent_id,
            message_type=MessageType.AI,
            name=self.default_agent_main.name,
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
                status_code=503, detail="Ошибка сохранения сообщения в чате"
            )

        return [message]
