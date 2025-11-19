"""
Автоматическое сканирование и анализ Telegram группы через GigaChat MAX
Сканирует группу каждый час, получает 200 последних сообщений, анализирует и отправляет отчёт
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from langchain_core.messages import SystemMessage, HumanMessage
from src.model.agent import Agent
from src.model.chat_models import GigaChatModel
from src.ai.managers.giga_chat_manager import get_giga_chat_manager

logger = logging.getLogger(__name__)


@dataclass
class TelegramScannerConfig:
    group_id: int = -2535311259                  # ID целевой группы (отрицательное число)
    user_id: int = 488356801                     # Your User ID для получения отчётов
    scan_period_secconds: int = 20
    messages_limit: int = 200         # Количество последних сообщений
    mcp_name: str = "telegram-mcp"         # Количество последних сообщений
    mcp_server_url: str = "http://127.0.0.1:8000/sse"  # MCP сервер
    mcp_transport: str = "sse"        # Тип транспорта (sse)


class TelegramGroupAnalyzer:
    
    def __init__(self, config: TelegramScannerConfig = TelegramScannerConfig()):
        self.config = config
        self.scheduler: Optional[AsyncIOScheduler] = None
        
        self.analyzer_agent = Agent(
            agent_id="telegram_analyzer",
            provider="gigachat",
            name="Telegram Group Analyzer",
            temperature=0.5,
            model=GigaChatModel.MAX.value,
            max_tokens=8000,
        )
        
        logger.info(f"TelegramGroupAnalyzer инициализирован для группы {config.group_id}")
    
    async def initialize_scheduler(self) -> None:
        self.scheduler = AsyncIOScheduler()
        
        self.scheduler.add_job(
            self._scan_and_report,
            IntervalTrigger(seconds=self.config.scan_period_secconds),
            id="telegram_scan_hourly",
            name="периодическое сканирование Telegram группы",
            replace_existing=True,
            misfire_grace_time=60,
        )
        
        self.scheduler.start()
        logger.info(
            f"✅ Scheduler запущен. Сканирование группы каждые {self.config.scan_period_secconds} секунд"
        )
    
    async def shutdown_scheduler(self) -> None:
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("❌ Scheduler остановлен")
    
    async def _scan_and_report(self) -> None:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"🔍 Начало сканирования группы {self.config.group_id} [{timestamp}]")
            
            # Формируем prompt для агента с инструкциями
            system_prompt = self._build_system_prompt()
            user_query = self._build_user_query()
            
            result = await get_giga_chat_manager().invoke_with_tools(
                connections={
                    self.config.mcp_name : {
                        "url": self.config.mcp_server_url,
                        "transport": self.config.mcp_transport,
                    }
                },
                agent=self.analyzer_agent,
                input_messages=(system_prompt + user_query),
            )
            
            # Извлекаем результат анализа
            report_content = str(result.message.content)
            
            logger.info(f"✅ Анализ завершён. Отправка отчёта пользователю {self.config.user_id}")
            
            # Отправляем отчёт в личку
            await self._send_report_to_user(report_content, timestamp)
            
            # Логируем затраты на токены
            logger.info(
                f"📊 Токены: prompt={result.prompt_tokens}, "
                f"completion={result.completion_tokens}, "
                f"cost={result.price:.4f}₽, "
                f"time={result.request_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сканировании: {e}", exc_info=True)
            await self._send_error_notification(str(e))
    
    def _build_system_prompt(self) -> str:
        """Конструирует системный prompt для агента"""
        return f"""Ты - аналитик Telegram группы. Твоя задача:

1. Используя доступные инструменты Telegram (из MCP сервера), получи последние {self.config.messages_limit} сообщений из группы {self.config.group_id}
2. Проанализируй контент сообщений (текст, ссылки, упоминания пользователей, тему обсуждений)
3. Выделить ключевые темы и интересные моменты
4. Создать краткую суммаризацию основного контента
5. Все результаты отправить пользователю {self.config.user_id} в личное сообщение

Формат отчёта должен быть структурированный и удобочитаемый."""
    
    def _build_user_query(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""Выполни следующую задачу:

1️⃣ Получи последние {self.config.messages_limit} сообщений из группы с ID {self.config.group_id}
2️⃣ Проанализируй сообщения и составь отчёт в формате:

📊 ОТЧЕТ СКАНИРОВАНИЯ TELEGRAM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Ключевые моменты:
[Перечисли самые интересные/важные моменты из группы]

📝 Полная суммаризация:
[Полный анализ контента, главные темы, активные пользователи]

📈 Статистика:
- Всего сообщений проанализировано: {self.config.messages_limit}
- Время сканирования: {timestamp}

3️⃣ Отправь этот отчёт пользователю {self.config.user_id} в личное сообщение

Используй доступные инструменты для получения сообщений и отправки отчёта."""
    
    async def _send_report_to_user(self, report: str, timestamp: str) -> None:
        """Отправляет готовый отчёт пользователю в личку"""
        # Этот метод вызовется агентом через MCP инструменты
        # Здесь логируем отправку для трекинга
        logger.info(
            f"📤 Отчёт отправлен пользователю {self.config.user_id}\n"
            f"Размер отчёта: {len(report)} символов\n"
            f"Время: {timestamp}"
        )
    
    async def _send_error_notification(self, error_msg: str) -> None:
        """Отправляет уведомление об ошибке"""
        error_report = f"""⚠️ ОШИБКА СКАНИРОВАНИЯ

Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Группа: {self.config.group_id}
Ошибка: {error_msg}

Попытка будет повторена в следующий."""
        
        logger.error(f"Отправка уведомления об ошибке: {error_report}")


class TelegramScannerService:
    """Сервис управления сканером (entry point)"""
    
    def __init__(self, config: TelegramScannerConfig):
        self.config = config
        self.analyzer = TelegramGroupAnalyzer(config)
    
    async def start(self) -> None:
        """Запускает сервис в фоне"""
        await self.analyzer.initialize_scheduler()
        logger.info("🚀 TelegramScannerService запущен")
    
    async def stop(self) -> None:
        """Останавливает сервис"""
        await self.analyzer.shutdown_scheduler()
        logger.info("🛑 TelegramScannerService остановлен")
    
    async def run_scan_now(self) -> None:
        """Немедленно запускает сканирование (для тестирования)"""
        logger.info("⚡ Запуск сканирования по требованию...")
        await self.analyzer._scan_and_report()


_scanner_service: Optional[TelegramScannerService] = None
_scanner_task: Optional[asyncio.Task] = None


def get_scanner_service() -> TelegramScannerService:
    global _scanner_service
    if _scanner_service is None:
        _scanner_service = TelegramScannerService(TelegramScannerConfig())
    return _scanner_service



async def _start_scanner_background() -> None:
    """Запускает сканер в фоне (помощник для background task)"""
    try:
        service = get_scanner_service()
        logger.info("🚀 Запуск сканера в фоне...")
        
        # Запускаем сканер (он будет работать в фоне с AsyncIOScheduler)
        await service.start()
        
        # Сканер работает в фоне, эта корутина не завершится
        # пока не вызовется stop_scanner_service()
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске сканера: {e}", exc_info=True)
    finally:
        try:
            service = get_scanner_service()
            await service.stop()
            logger.info("✅ Сканер остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке сканера: {e}")


async def start_scanner_service() -> None:
    """
    Запускает сканер в отдельной background task
    Не блокирует основное приложение
    """
    global _scanner_task
    
    # Проверь что сканер уже не запущен
    if _scanner_task and not _scanner_task.done():
        logger.warning("⚠️  Сканер уже запущен!")
        return
    
    logger.info("📝 Создание background task для сканера...")
    
    # Создаём задачу в фоне
    _scanner_task = asyncio.create_task(_start_scanner_background())
    
    logger.info("✅ Background task создана, сканер запускается...")


async def stop_scanner_service() -> None:
    """
    Останавливает работающий сканер
    """
    global _scanner_task
    
    service = get_scanner_service()
    await service.stop()
    
    # Отмени background task если она ещё работает
    if _scanner_task and not _scanner_task.done():
        _scanner_task.cancel()
        try:
            await _scanner_task
        except asyncio.CancelledError:
            logger.info("Background task отменена")
    
    logger.info("✅ Сканер остановлен")
