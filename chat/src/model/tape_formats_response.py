from enum import Enum


class FormatType(str, Enum):
    JSON = "[JSON]"
    XML = "[XML]"
    DEFAULT = "[DEFAULT]"