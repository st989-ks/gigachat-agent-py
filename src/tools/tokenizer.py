import logging
import os
from typing import Dict, Optional, Any
from transformers import AutoTokenizer
import tiktoken

logger = logging.getLogger(__name__)


class TokenCounter:

    def __init__(self) -> None:
        self._tokenizers: Dict[str, Any] = {}
        self._model_map = {
            # Ollama models -> HuggingFace tokenizer equivalents
            "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "mistral:7b": "mistralai/Mistral-7B-v0.1",
            "llama2:13b": "meta-llama/Llama-2-13b-hf",

            # HuggingFace models -> themselves
            "mistralai/Mistral-7B-Instruct-v0.2": "mistralai/Mistral-7B-Instruct-v0.2",
            "meta-llama/Llama-3.1-8B-Instruct": "meta-llama/Llama-3.1-8B-Instruct",
            "google/flan-t5-large": "google/flan-t5-large",
            "Sao10K/L3-8B-Stheno-v3.2": "Sao10K/L3-8B-Stheno-v3.2",
        }

    def _get_tokenizer(self, model_name: str) -> Any:
        """Получить или загрузить tokenizer с кешированием"""
        if model_name in self._tokenizers:
            logger.info(f"загрузить tokenizer for {model_name}")
            return self._tokenizers[model_name]

        # Маппинг на HuggingFace model
        hf_model = self._model_map.get(model_name, model_name)

        try:
            logger.info(f"AutoTokenizer.from_pretrained -> {hf_model}")
            api_key = os.getenv("HF_TOKEN")
            os.environ["HF_HUB_DISABLE_XET"] = "1"
            tokenizer = AutoTokenizer.from_pretrained(
                pretrained_model_name_or_path =hf_model,
                token=api_key,
                trust_remote_code=True,
                local_files_only=True
            )
            self._tokenizers[model_name] = tokenizer
            logger.info(f"Loaded tokenizer for {model_name} (mapped to {hf_model})")
            return tokenizer
        except Exception as e:
            logger.warning(f"Failed to load tokenizer for {model_name}: {e}, using tiktoken")
            # Fallback to tiktoken (GPT tokenizer)
            encoding = tiktoken.get_encoding("cl100k_base")
            self._tokenizers[model_name] = encoding
            return encoding

    def count_tokens(self, text: str, model_name: str) -> int:
        """Подсчитать количество токенов в тексте"""
        logger.info(f"Loaded tokenizer for {model_name}")
        tokenizer = self._get_tokenizer(model_name)

        # Для transformers tokenizer
        if hasattr(tokenizer, 'encode'):
            logger.info(f"Для transformers tokenizer for {model_name}")
            return len(tokenizer.encode(text))
        # Для tiktoken
        elif hasattr(tokenizer, 'encode'):
            logger.info(f"Для tokenizer for {model_name}")
            return len(tokenizer.encode(text))
        else:
            # Fallback: примерная оценка (1 token ≈ 4 chars)
            logger.info(f"примерная оценка for {model_name}")
            return len(text) // 4

    def count_message_tokens(self, messages: list, model_name: str) -> int:
        """Подсчитать токены для списка сообщений"""
        total = 0
        for msg in messages:
            if hasattr(msg, 'content'):
                total += self.count_tokens(msg.content, model_name)
            else:
                total += self.count_tokens(str(msg), model_name)
        return total


# Singleton
_token_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    global _token_counter
    if _token_counter is None:
        _token_counter = TokenCounter()
    return _token_counter
