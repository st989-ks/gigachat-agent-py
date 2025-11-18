import logging
import sys


def setup_logging() -> None:
    """
    Настройка корневого логгера: вывод в stdout, уровень INFO, формат.
    """
    log_level = logging.INFO
    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, date_format))

    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)

    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    logging.info("🚀 Приложение запускается...")
