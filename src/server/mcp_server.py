from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel
import sympy
import logging
import os

logger = logging.getLogger(__name__)

server = FastAPI(title="Local MCP Server", version="1.0", docs_url="/docs")

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str

class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict

class ExecuteRequest(BaseModel):
    expression: str

class ExecutionResult(BaseModel):
    result: float

TOOLS = [
    Tool(name="calculate", description="Вычисляет математические выражения.", input_schema={"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}),
    Tool(name="add", description="Складывает два числа.", input_schema={"type": "object", "properties": {"num1": {"type": "number"}, "num2": {"type": "number"}}, "required": ["num1", "num2"]}),
    Tool(name="multiply", description="Умножает два числа.", input_schema={"type": "object", "properties": {"num1": {"type": "number"}, "num2": {"type": "number"}}, "required": ["num1", "num2"]}),
    Tool(name="power", description="Возводит число в степень.", input_schema={"type": "object", "properties": {"base": {"type": "number"}, "exponent": {"type": "number"}}, "required": ["base", "exponent"]})
]

@server.get("/health", response_model=HealthCheckResponse)
async def health_check():
    logger.info("📥 Запрос на проверку состояния сервера.")
    return HealthCheckResponse(status="OK", timestamp=str(datetime.now()))

@server.get("/tools", response_model=List[Tool])
async def get_tools():
    logger.info("📥 Запрошен список инструментов.")
    return TOOLS

@server.post("/execute/{tool_name}", response_model=ExecutionResult)
async def execute_tool(tool_name: str, req: ExecuteRequest):
    logger.info(f"📥 Выполнение инструмента {tool_name}. Параметры: {req.dict()}")
    try:
        if tool_name == "calculate":
            result = float(sympy.sympify(req.expression))
        elif tool_name == "add":
            num1, num2 = map(float, req.expression.split(","))
            result = num1 + num2
        elif tool_name == "multiply":
            num1, num2 = map(float, req.expression.split(","))
            result = num1 * num2
        elif tool_name == "power":
            base, exponent = map(float, req.expression.split(","))
            result = pow(base, exponent)
        else:
            raise ValueError(f"Неверное имя инструмента: {tool_name}")
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения инструмента {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    logger.info(f"✅ Инструмент {tool_name} выполнен успешно. Результат: {result}")
    return ExecutionResult(result=result)
```

---

### 2️⃣ Клиент MCP (`src/ai/mcp_client.py`)
Клиент поддерживает подключение к нескольким серверам и кэширует полученные инструменты.

src/ai/mcp_client.py
