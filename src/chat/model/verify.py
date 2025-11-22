from pydantic import BaseModel, Field


class AuthResponse(BaseModel):
    password: str = Field(..., description="Пароль для авторизации")