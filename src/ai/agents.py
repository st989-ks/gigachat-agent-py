from enum import Enum


class AgentId(str, Enum):
    STANDARD = "<standard>"
    FORMATTER = "<formatter>"
    QUESTIONER = "<questioner>"
    TECHNICAL_SPECIFICATION = "<technical_specification>"
    NAGGING_ANALYST = "<nagging_analyst>"
    FACE_TERMS_OF_REFERENCE = "<face_terms_of_reference>"
