import os
from pathlib import Path
from typing import Optional, Final

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DEBUG: Final[bool] = True
    VERSION: Final[str] = "1.0.0"

    def __init__(self) -> None:
        self.debug: bool = Settings.DEBUG
        self.version: str = Settings.VERSION

        self.PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent
        self.LOGS_DIR: Path = self.PROJECT_ROOT / "logs"
        self.DATA_DIR: Path = self.PROJECT_ROOT / "data"
        self.SITE_DIR: Path = self.PROJECT_ROOT / "web"
        self.SESSIONS_DIR: Path = self.DATA_DIR / "sessions"
        self.DB_DIR: Path = self.DATA_DIR / "db"
        self.AGENTS_LOG_FILE: Path = self.LOGS_DIR / "agents.log"

        # Создаём директории при импорте если их нет
        for directory in [self.LOGS_DIR, self.DATA_DIR, self.AGENTS_LOG_FILE, self.SESSIONS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

        # Ключ авторизации берется из переменной окружения
        self.AUTH_KEY: str = os.getenv("GIGACHAT_TOKEN", "")

        # Область доступа - для физических лиц
        self.SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

        # URL для получения OAuth токена
        self.OAUTH_URL: str = os.getenv("GIGACHAT_OAUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")

        # Базовый URL GigaChat API
        self.BASE_URL: str = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")

        self.CORS_ALLOWED_HOSTS: list[str] | None = ["http://localhost:5173"]

        # ===== Настройки сертификатов =====
        # Путь к файлу сертификата НУЦ Минцифры
        # https://developers.sber.ru/docs/ru/gigachat/certificates
        # Сертификат необходим для безопасного соединения с GigaChat API
        # None означает, что сертификат не установлен на уровне приложения
        self.CERTIFICATE_PATH: Optional[str] = os.getenv(
            "CERTIFICATE_PATH")  # Здесь можно указать путь к файлу сертификата, например:
        # CERTIFICATE_PATH = "/cert/russian_trusted_root_ca_pem.crt"


settings = Settings()
