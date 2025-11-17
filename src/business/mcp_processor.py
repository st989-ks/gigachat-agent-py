import logging
from typing import List, Optional, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from src.ai.mcp_client import MCPClient
from src.ai.mcp_tool_converter import MCPToolConverter
from src.business.mcp_gigachat_agent import MCPGigaChatAgent
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
        self.mcp_client = MCPClientV2([
            MCPServerConfig(name="local", url="http://localhost:8010"),
        ])
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
        if self.user_message_text.strip().lower() == "/seetools":
            tools = await self.mcp_client.get_all_tools()
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

        agent = MCPGigaChatAgent(self.default_agent, self.mcp_client)
        await agent.initialize()
        processed_output = await agent.process_with_tools(HumanMessage(content=self.user_message_text))
        response = Message(
            id=None,
            chat_id=self.message_user.chat_id,
            session_id=self.message_user.session_id,
            agent_id=self.default_agent.agent_id,
            message_type=MessageType.AI,
            name=self.default_agent.name,
            timestamp=get_time_now_h_m_s(),
            message=processed_output.message,
            prompt_tokens=0,
            completion_tokens=0,
            request_time=0,
            price=0,
            meta="Ответ обработан агентом"
        )
        await get_db_manager().add_message(response)
        return MessageList(messages=[response])