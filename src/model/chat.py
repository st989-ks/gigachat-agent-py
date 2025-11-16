from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Chat(BaseModel):
    id: str = Field(..., description="Unique identifier of the chat")
    system_prompt: Optional[str] = Field(None, description="Prompt used by the chat")
    name: str = Field(..., description="Title of the chat")
    created_at: Optional[datetime] = Field(
        None, description="Date and time when the chat was created"
    )


class ChatList(BaseModel):
    chats: list[Chat] = Field(..., description="Список агентных систем")


class ChatIdRequest(BaseModel):
    id: str = Field(..., description="Unique identifier of the chat")
