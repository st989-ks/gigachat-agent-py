import os

# Ключ авторизации берется из переменной окружения
AUTH_KEY = os.getenv("GIGACHAT_TOKEN")

# Область доступа - для физических лиц
SCOPE = "GIGACHAT_API_PERS"

# Проверка наличия ключа авторизации при импорте модуля
if not AUTH_KEY:
    raise RuntimeError(
        "❌ Переменная окружения GIGACHAT_TOKEN не установлена.\n"
        "Пожалуйста, установите её командой:\n"
        "export GIGACHAT_TOKEN='ваш_ключ_авторизации'"
    )

# URL для получения OAuth токена
OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

# Базовый URL GigaChat API
BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"

# ===== Настройки сертификатов =====
# Путь к файлу сертификата НУЦ Минцифры
# Сертификат необходим для безопасного соединения с GigaChat API
# None означает, что сертификат не установлен на уровне приложения
CERTIFICATE_PATH = None  # Здесь можно указать путь к файлу сертификата, например:
# CERTIFICATE_PATH = "/cert/russian_trusted_root_ca_pem.crt"