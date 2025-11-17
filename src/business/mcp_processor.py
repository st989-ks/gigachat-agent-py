"""
Обработчик для работы с MCP инструментами в контексте чата.
"""

import logging
import re
from typing import List, Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from src.ai.mcp_client import MCPClient, MCPTool
from src.db.db_manager import get_db_manager
from src.model.agent import Agent
from src.model.chat import Chat
from src.model.chat_models import ModelProvideType, GigaChatModel
from src.model.messages import (
    Message,
    MessageRequest,
    MessageList,
    MessageType,
)
from src.tools.time import get_time_now_h_m_s

logger = logging.getLogger(__name__)

class MCPProcessor:
    """
    Процессор для обработки сообщений через MCP инструменты.
    
    Логика:
    1. Получает сообщение пользователя
    2. Определяет нужный инструмент из доступных
    3. Выполняет инструмент через MCP
    4. Сохраняет результат как сообщение AI
    """
    
    default_agent: Agent = Agent(
        agent_id="MCP_Agent",
        name="MCP Tools Agent",
        provider=ModelProvideType.GIGA_CHAT.value,
        temperature=0.3,
        model=GigaChatModel.STANDARD.value,
        max_tokens=1000,
    )
    
    def __init__(
        self,
        session_id: str,
        chat: Chat,
        value: MessageRequest,
    ):
        self.chat = chat
        self.session_id = session_id
        self.user_message_text = value.message
        self.mcp_client = MCPClient()
        
        self.message_user = Message(
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
        """Основной метод обработки сообщения через MCP"""

        # Если пользователь в сообщении отправил текст "/seetools" 
        # то надо получить список инструментов с описанием через MCPClient 
        # и вернуть его без сохранения
        if self.user_message_text.strip().lower() == "/seetools":
            tools = await self.mcp_client.get_tools()
            response_text = "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
            response = Message(
                id=None,
                chat_id=self.message_user.chat_id,
                session_id=self.message_user.session_id,
                agent_id=self.default_agent.agent_id,
                message_type=MessageType.AI,
                name=self.default_agent.name,
                timestamp=get_time_now_h_m_s(),
                message=response_text,
                prompt_tokens=0,
                completion_tokens=0,
                request_time=0,
                price=0,
                meta="Список инструментов MCP"
            )
            return MessageList(messages=[response])
        
        # Получаем доступные инструменты
        tools = await self.mcp_client.get_tools()
        
        # Определяем нужный инструмент
        selected_tool = self._parse_tool_request(self.user_message_text, tools)
        
        if not selected_tool:
            # Если инструмент не определен, возвращаем ошибку
            response = Message(
                id=None,
                chat_id=self.message_user.chat_id,
                session_id=self.message_user.session_id,
                agent_id=self.default_agent.agent_id,
                message_type=MessageType.AI,
                name=self.default_agent.name,
                timestamp=get_time_now_h_m_s(),
                message="Не удалось определить нужный инструмент. Доступные инструменты: " + ", ".join([t.name for t in tools]),
                prompt_tokens=0,
                completion_tokens=0,
                request_time=0,
                price=0,
                meta="Инструмент не найден"
            )
        else:
            try:
                await get_db_manager().add_message(self.message_user)
            except Exception as e:
                logger.error(f"Ошибка сохранения сообщения пользователя: {e}")
                raise

            # Выполняем инструмент
            params = self._extract_params(self.user_message_text)
            
            try:
                result = await self.mcp_client.execute(selected_tool.name, params)
                response_text = f"Результат выполнения инструмента '{selected_tool.name}':\\n{result}"
                response = Message(
                    id=None,
                    chat_id=self.message_user.chat_id,
                    session_id=self.message_user.session_id,
                    agent_id=self.default_agent.agent_id,
                    message_type=MessageType.AI,
                    name=self.default_agent.name,
                    timestamp=get_time_now_h_m_s(),
                    message=response_text,
                    prompt_tokens=0,
                    completion_tokens=0,
                    request_time=0,
                    price=0,
                    meta=f"Инструмент: {selected_tool.name}"
                )
            except Exception as e:
                logger.error(f"Ошибка выполнения инструмента: {e}")
                response_text = f"Ошибка выполнения инструмента: {str(e)}"
                response = Message(
                    id=None,
                    chat_id=self.message_user.chat_id,
                    session_id=self.message_user.session_id,
                    agent_id=self.default_agent.agent_id,
                    message_type=MessageType.AI,
                    name=self.default_agent.name,
                    timestamp=get_time_now_h_m_s(),
                    message=response_text,
                    prompt_tokens=0,
                    completion_tokens=0,
                    request_time=0,
                    price=0,
                    meta=f"Ошибка выполнения инструмента"
                )
        
        # Сохраняем ответ

        db_response: Optional[Message] = await get_db_manager().add_message(response) 
        if not db_response:
            logger.error("Ошибка сохранения ответа")
            return MessageList(messages=[response])

        return MessageList(messages=db_response) # type: ignore
 
           
    @staticmethod
    def _parse_tool_request(message: str, tools: List[MCPTool]) -> Optional[MCPTool]:
        """
        Определить нужный инструмент из сообщения пользователя.
        Простая реализация на основе ключевых слов.
        """
        message_lower = message.lower()
        
        for tool in tools:
            if tool.name.lower() in message_lower:
                return tool
        
        return None
    
    @staticmethod
    def _extract_params(message: str) -> Dict[str, Any]:
        """Извлечь параметры для инструмента из сообщения"""
        # Простая реализация - парсим JSON-подобные параметры
        params = {}
        
        # Ищем pattern: param=value
        matches = re.findall(r'(\w+)\s*=\s*([^,\s]+)', message)
        for key, value in matches:
            # Пытаемся привести значение к подходящему типу
            if value.isdigit():
                params[key] = int(value)
            elif value.lower() in ('true', 'false'):
                params[key] = value.lower() == 'true'
            else:
                params[key] = value
        
        return params
