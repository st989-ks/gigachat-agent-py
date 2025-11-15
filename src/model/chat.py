from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Chat(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier of the chat")
    name: str = Field(..., description="Title of the chat")
    created_at: Optional[datetime] = Field(default=None, description="Date and time when the chat was created")

    class Config:
        orm_mode = True