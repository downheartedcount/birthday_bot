from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    CHAT_FILE: str = "chat.json"
    EMPLOYEE_FILE: str = "employee.json"
    HOUR: int = 8
    MINUTE: int = 0

    class Config:
        env_file = ".env"


settings = Settings()
