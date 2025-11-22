import asyncio
import logging
import time

from typing import Dict

from pandas import DataFrame
from langchain_core.messages import HumanMessage, SystemMessage

from src.chat.ai.managers.huggingface_manager import get_hf_manager
from src.chat.ai.managers.ollama_manager import get_ollama_manager
from src.chat.core.configs import settings
from src.chat.core.logging_config import setup_logging
from src.chat.model.agent import Agent
from src.chat.model.chat_models import OllamaModel, HuggingFaceModel
from src.chat.tools.tokenizer import get_token_counter

# Конфигурация тестов
TEST_PROMPT = "Объясни разницу между машинным обучением и глубоким обучением простыми словами."
SYSTEM_PROMPT = "Ты - помощник, который объясняет сложные концепции простым языком."
MAX_TOKENS = 512
TEMPERATURE = 0

MODELS_TO_TEST: list[Agent] = [
    # Ollama models
    Agent(
        agent_id="test_ollama_tiny",
        provider="ollama",
        name="tinyllama:latest",
        temperature=TEMPERATURE,
        model=OllamaModel.TINYLLAMA.value,
        max_tokens=MAX_TOKENS
    ),
    Agent(
        agent_id="test_ollama_mistral",
        provider="ollama",
        name="mistral:7b",
        temperature=TEMPERATURE,
        model=OllamaModel.MISTRAL_7B.value,
        max_tokens=MAX_TOKENS
    ),
    Agent(
        agent_id="test_ollama_llama2",
        provider="ollama",
        name="llama2:13b",
        temperature=TEMPERATURE,
        model=OllamaModel.LLAMA2_13B.value,
        max_tokens=MAX_TOKENS
    ),

    # HuggingFace models
    Agent(
        agent_id="test_hf_mistral",
        provider="huggingface",
        name=HuggingFaceModel.MISTRAL_7B_INSTRUCT.value,
        temperature=TEMPERATURE,
        model=HuggingFaceModel.MISTRAL_7B_INSTRUCT.value,
        max_tokens=MAX_TOKENS
    ),

    Agent(
        agent_id="test_hf_llama",
        provider="huggingface",
        name=HuggingFaceModel.LLAMA_3_1_8B_INSTRUCT.value,
        temperature=TEMPERATURE,
        model=HuggingFaceModel.LLAMA_3_1_8B_INSTRUCT.value,
        max_tokens=MAX_TOKENS
    ),

    Agent(
        agent_id="test_hf_sao10k",
        provider="huggingface",
        name=HuggingFaceModel.SAO10K_L3_8B_STHENO_V3_2.value,
        temperature=TEMPERATURE,
        model=HuggingFaceModel.SAO10K_L3_8B_STHENO_V3_2.value,
        max_tokens=MAX_TOKENS
    ),
]


async def run_model(agent: Agent) -> Dict:
    """Тест одной модели с замером метрик"""
    print(f"\n{'='*60}")
    print(f"🧪 Тестируем: {agent.name}")
    print(f"{'='*60}")


    # Подготавливаем сообщения
    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(TEST_PROMPT)
    ]

    # Подсчитываем входные токены
    token_counter = get_token_counter()
    logging.info(f"token_counter for {agent.provider}")
    input_tokens = token_counter.count_message_tokens(messages, agent.name)

    # Запускаем с замером времени
    start_time = time.time()
    logging.info(f"start_time for {agent.provider}")
    try:
        if agent.provider == "ollama":
            manager = get_ollama_manager()
            response = await manager.ainvoke(agent, messages)
        elif agent.provider == "huggingface":
            manager = get_hf_manager()  # type: ignore
            response = await manager.ainvoke(agent, messages)
        else:
            raise ValueError(f"Unknown provider: {agent.provider}")

        response_time = time.time() - start_time

        # Подсчитываем выходные токены
        response_text: str = str(response.content) if hasattr(response, 'content') else str(response)
        output_tokens = token_counter.count_tokens(response_text, agent.model)
        total_tokens = input_tokens + output_tokens

        print(f"✅ Успешно! Время: {response_time:.2f}s")
        print(f"📊 Токены: Input={input_tokens}, Output={output_tokens}, Total={total_tokens}")
        print(f"💬 Ответ (первые 200 символов):\n{response_text[:200]}...")

        return {
            "model": agent.name,
            "provider": agent.provider,
            "response_time_s": round(response_time, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "response": response_text,
            "status": "success"
        }

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {
            "model": agent.name,
            "provider": agent.provider,
            "response_time_s": -1,
            "input_tokens": input_tokens,
            "output_tokens": 0,
            "total_tokens": input_tokens,
            "response": f"ERROR: {str(e)}",
            "status": "error"
        }


async def main()->None:
    setup_logging()
    """Основная функция для запуска сравнения"""
    print("🚀 Начинаем сравнение моделей...")
    print(f"📝 Тестовый промпт: {TEST_PROMPT}\n")

    results = []

    # Запускаем тесты последовательно (можно распараллелить, но API rate limits)
    for model_config in MODELS_TO_TEST:
        result = await run_model(model_config)
        results.append(result)

        # Пауза между запросами (уважаем API rate limits)
        await asyncio.sleep(2)

    # Создаем DataFrame и сохраняем
    df = DataFrame(results)

    print("\n" + "="*80)
    print("📊 ИТОГОВАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ:")
    print("="*80)
    print(df[['model', 'provider', 'response_time_s', 'input_tokens',
              'output_tokens', 'total_tokens', 'status']].to_string(index=False))

    # Сохраняем в CSV
    csv_filename = f"model_comparison_results_{int(time.time())}.csv"
    df.to_csv(str(settings.DATA_DIR / csv_filename), index=False, encoding='utf-8')
    print(f"\n✅ Результаты сохранены в: {csv_filename}")

    # Краткий вывод - топ модели
    print("\n" + "="*80)
    print("🏆 МОДЕЛИ:")
    print("="*80)

    successful = df[df['status'] == 'success']
    if not successful.empty:
        print(f"⚡ Самая быстрая: {successful.loc[successful['response_time_s'].idxmin(), 'model']} "
              f"({successful['response_time_s'].min():.2f}s)")
        print(f"💰 Наименьший расход токенов: {successful.loc[successful['total_tokens'].idxmin(), 'model']} "
              f"({successful['total_tokens'].min()} tokens)")


if __name__ == "__main__":
    asyncio.run(main())
