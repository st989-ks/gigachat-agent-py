from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class MCPTool(BaseModel):
    name: str = Field(..., description="Имя инструмента")
    description: str = Field(..., description="Описание инструмента")
    input_schema: Dict = Field(..., description="JSON схема входных параметров инструмента")

class MCPServerConfig(BaseModel):
    name: str = Field(..., description="Название сервера")
    url: str = Field(..., description="URL сервера")
    description: str = Field("", description="Дополнительное описание сервера")

class ToolExecutionResult(BaseModel):
    tool_name: str = Field(..., description="Имя выполненного инструмента")
    success: bool = Field(True, description="Флаг успешного выполнения")
    result: Optional[Union[str, float]] = Field(None, description="Результат выполнения инструмента")
    error: Optional[str] = Field(None, description="Сообщение об ошибке, если есть")
    execution_time: float = Field(..., description="Время выполнения инструмента в секундах")
```

src/ai/mcp_client_v2.py
