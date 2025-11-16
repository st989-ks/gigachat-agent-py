from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

class Agent(BaseModel):
    agent_id: str = Field(..., description="ID агента")
    provider: str = Field(..., description="Вид LLM")
    name: str = Field(..., description="Имя агента")
    temperature: float = Field(..., description="Температура агента")
    model: str = Field(..., description="Модель для агента")
    max_tokens: Optional[int] = Field(..., description="Максимальное колличество токенов с которыми работает агент")