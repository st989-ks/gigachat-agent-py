from enum import Enum
from typing import List, Optional

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    AI = "AI"


class MessageRequest(BaseModel):
    message: str = Field(..., description="послание для АИ")


class Message(BaseModel):
    id: Optional[int] = Field(None, description="ID сообщения")
    chat_id: str = Field(..., description="ID of the chat associated with the message")
    session_id: str = Field(..., description="Id сессии")
    message_type: MessageType = Field(..., description="Типы сообщений")
    agent_id: Optional[str] = Field(..., description="Id агента, если это он")
    name: str = Field(..., description="имя тела, которое написало сообщение")
    timestamp: str = Field(..., description="время сообщения")
    message: str = Field(..., description="сообщение")
    prompt_tokens: int = Field(..., description="Количество отправляемых токенов")
    completion_tokens: int = Field(..., description="Количество принимаемых токенов")
    request_time: float = Field(..., description="Время запроса")
    price: float = Field(..., description="Цена")
    meta: str = Field(..., description="Дополнительная информация")


class MessageList(BaseModel):
    messages: List[Message] = Field(..., description="список сообщений")


class MessageOutput(BaseModel):
    message: BaseMessage = Field(..., description="Сообщение")
    prompt_tokens: int = Field(..., description="Количество отправляемых токенов")
    completion_tokens: int = Field(..., description="Количество принимаемых токенов")
    request_time: float = Field(..., description="Время запроса")
    price: float = Field(..., description="Цена")
    meta: str = Field(..., description="Дополнительная информация")
