from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    message: str =  Field(..., description="Ответ на запрос")
    success: bool = Field(default=True, description="Выполнен ли был запрос в полной мере")