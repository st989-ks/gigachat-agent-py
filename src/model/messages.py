from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

class MessageType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    AI = "AI"

class MessageRequest(BaseModel):
    message: str = Field(..., description="послание для АИ")


class Message(BaseModel):
    id: Optional[int] = Field(None, description="ID сообщения")
    session_id: str = Field(..., description="Id сессии")
    message_type: MessageType = Field(..., description="Типы сообщений")
    agent_id: Optional[str] = Field(..., description="Id агента, если это он")
    name: str = Field(..., description="имя тела, которое написало сообщение")
    timestamp: str = Field(..., description="время сообщения")
    message: str = Field(..., description="сообщение")


class MessageList(BaseModel):
    messages: List[Message] = Field(..., description="список сообщений")
