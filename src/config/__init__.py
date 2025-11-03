"""
Модуль для определения доступных моделей GigaChat  и настроек приложения..

Содержит перечисление (enum) всех поддерживаемых моделей GigaChat
и их настройки по умолчанию, конфигурационные параметры приложения,
включая URL API, ключи авторизации и пути к сертификатам.

Переменные окружения:
    GIGACHAT_TOKEN: Ключ авторизации GigaChat API (обязательно)

Пример:
    export GIGACHAT_TOKEN="ваш_ключ_авторизации"

Пример использования:
    from config.models import GigaChatModel

    model_name = GigaChatModel.GIGACHAT_2_MAX.value
    print(model_name)  # Выведет: "GigaChat-2-Max"
"""