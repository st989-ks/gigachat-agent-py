from enum import Enum


class GigaChatModel(str, Enum):
    STANDARD = "GigaChat-2"
    PRO = "GigaChat-2-Pro"
    MAX = "GigaChat-2-Max"
