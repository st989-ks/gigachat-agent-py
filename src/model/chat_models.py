from enum import Enum


class GigaChatModel(str, Enum):
    STANDARD = "GigaChat-2"
    PRO = "GigaChat-2-Pro"
    MAX = "GigaChat-2-Max"


class OllamaModel(str, Enum):

    TINYLLAMA = "tinyllama:latest"
    MISTRAL_7B = "mistral:7b"
    LLAMA2_13B = "llama2:13b"

    # Дополнительные модели (опционально)
    NEURAL_CHAT = "neural-chat:7b"
    STARLING = "starling-lm:7b"
    OPENCHAT = "openchat:7b"

class OllamaTaskType(str, Enum):

    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    SUMMARIZATION = "summarization"


class HuggingFaceModel(str, Enum):
    MISTRAL_7B_INSTRUCT = "mistralai/Mistral-7B-Instruct-v0.2"
    LLAMA_3_1_8B_INSTRUCT = "meta-llama/Llama-3.1-8B-Instruct"
    FLAN_T5_LARGE = "google/flan-t5-large"
    SAO10K_L3_8B_STHENO_V3_2 = "Sao10K/L3-8B-Stheno-v3.2"
    MINI_MAX_M2 = "MiniMaxAI/MiniMax-M2"
    QWEN2_5_VL_7B = "Qwen/Qwen2.5-VL-7B-Instruct"
