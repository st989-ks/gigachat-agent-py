import logging

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage

from src.ai.managers.giga_chat_manager import get_giga_chat_manager
from src.db.db_manager import get_db_manager
from src.model.agent import Agent
from src.model.chat_models import GigaChatModel
from src.model.messages import Message, MessageRequest, MessageType, MessageList
from src.tools.time import get_time_now_h_m_s

logger = logging.getLogger(__name__)


class ProcessDay5:
    system_prompt = (
        "Ты талантливый философ. Роль:\n"
        "1) Отвечать на вопросы, с размышнением.\n"
        "4) Будь дружелюбным, точным, информативным, и лаконичный, допускается дружественная дерзость\n"
    )

    def __init__(
            self,
            session_id: str,
            value: MessageRequest,
    ):
        self.session_id: str = session_id
        self.message_user: str = value.message

    async def process(self) -> MessageList:
        await self.add_message_in_db()
        first_response = await self._process_response(GigaChatModel.STANDARD)
        second_response = await self._process_response(GigaChatModel.PRO)
        third_response = await self._process_response(GigaChatModel.MAX)

        forth_response = await self._process_master_response([
            first_response,
            second_response,
            third_response
        ])

        message: Message = Message(
            id=None,
            session_id=self.session_id,
            message_type=MessageType.AI,
            agent_id=None,
            name="MULTI AI",
            timestamp=get_time_now_h_m_s(),
            message=first_response + second_response + third_response + forth_response,
        )
        message = await get_db_manager().add_message(message)  # type: ignore

        return message

    async def add_message_in_db(self) -> None:
        message: Message = Message(
            id=None,
            session_id=self.session_id,
            message_type=MessageType.USER,
            agent_id=None,
            name="User",
            timestamp=get_time_now_h_m_s(),
            message=self.message_user,
        )
        await get_db_manager().add_message(message)

    async def _process_response(self, model: GigaChatModel) -> str:
        agent_1 = Agent(
            agent_id="Custom",
            name=f"{model.name} 0",
            provider="gigachat",
            temperature=0,
            model=model.value,
            system_prompt=self.system_prompt,
            max_tokens=None,
        )

        agent_2 = Agent(
            agent_id="Custom",
            name=f"{model.name} 0.33",
            provider="gigachat",
            temperature=0.33,
            model=model.value,
            system_prompt=self.system_prompt,
            max_tokens=None,
        )

        agent_3 = Agent(
            agent_id="Custom",
            name=f"{model.name} 0",
            provider="gigachat",
            temperature=0.97,
            model=model.value,
            system_prompt=self.system_prompt,
            max_tokens=None,
        )

        agents = [
            agent_1,
            agent_2,
            agent_3,
        ]
        output = f"{'#' * 60}\n👥 ГРУППА ИИ : {model.name}\n{'#' * 60}\n\n"

        for agent in agents:
            try:
                prompt = get_giga_chat_manager().invoke(
                    agent=agent,
                    input_messages=[
                        SystemMessage(agent.system_prompt),
                        HumanMessage(self.message_user)
                    ],
                    config=None,
                    stop=None,
                )

                content = prompt.message if isinstance(prompt.message, str) else str(prompt.message)
                output += (f"{'=' * 60}\n🎭 temperature={agent.temperature}, "
                           f"model={agent.model}\n{'-' * 10}\n{content}\n\n\n\n")

            except Exception as e:
                output += f"❌ {agent.name}: {e}\n\n"

        return output

    async def _process_master_response(
            self,
            list_response: list[str]
    ) -> str:
        """
        Сравнение и консенсус — оркестратор агрегирует все ответы
        """
        agent = Agent(
            agent_id="Custom",
            name="Верховный судья",
            provider="gigachat",
            temperature=0.2,
            model=GigaChatModel.MAX.value,
            system_prompt=(
                """
                Ты — Верховный Судья (Grand Master Oracle), мудрый координатор совета искусственных интеллектов. 
                Тебе необходимо строго и беспристрастно сравнить ответы разных моделей ИИ на один вопрос, чтобы 
                определить сильные и слабые стороны каждой настройки, а также подсказать оптимальные применения для 
                их параметров (с акцентом на температуру и архитектуру). Главная цель — дать рекомендацию, какой тип 
                ответа/настроек лучше всего подходит для конкретных жизненно-философских и бытовых задач.
                
                ТВОЯ ИНСТРУКЦИЯ:
                
                1️⃣ Проанализируй и сравни каждый ответ эксперта. Для каждого укажи:
                - Какую настройку использовал эксперт (какая модель, температура и т.п.)?
                - В чем преимущества данного подхода — стиль, глубина, точность, оригинальность, практичность, 
                эмоциональность, структурированность.
                - В каких случаях или для каких подзадач такой стиль наиболее уместен? (например, креативный нужен для
                 генерации идей, строго-формальный — для инструкций, эмпатичный — для советов и т.п.)
                
                2️⃣ Сравни ответы между собой:
                - Какие заметны паттерны (например, высокая температура = креативнее, но менее структурировано)?
                - Для каких пользовательских задач ответ/настройка подходит лучше остальных?
                - Где настройки привели к недочетам (размытие смысла, чрезмерная формальность, поверхностность и т.д.)?
                
                3️⃣ Дай рекомендации:
                - Для каждой настройки/подхода рекомендации по применению: «Лучше всего использовать, когда...», 
                «Не подходит, если...», «Особенно отлично проявил себя в...»
                - Выдели универсальные настройки, если такие проявились.
                
                ФОРМАТ ОТВЕТА:
                
                ─────────────────────────
                🧠 Краткое резюме (3—5 строк):  
                [Обобщи — чем ответы различались, какие ключевые особенности показали разные настройки, 
                главный инсайт анализа.]
                
                🏆 Рекомендуемые настройки и задачи:  
                [Кратко выдели — какая настройка/модель/температура оптимальна для каких случаев, 
                с кратким обоснованием.]
                
                💡 Главный совет пользователю:  
                [Одна-две строки — как выбирать настройки в зависимости от целей и контекста.]
                
                ─────────────────────────
                
                ВАЖНО:
                - Не фаворизируй ни одну модель или температуру.
                - Точно указывай плюсы и минусы каждого варианта.
                - Всегда отражай, что универсальных ответов нет: все зависит от задачи, контекста 
                и ожиданий пользователя.
                - Не допускай субъективных предпочтений — фокусируйся на функциях, примерах применения и стиле.
                
                Только по существу. Кратко, структурировано. Никакой воды.
                """
            ),
            max_tokens=None,
        )

        messages: list[BaseMessage] = [
            SystemMessage(agent.system_prompt),
            HumanMessage(f"Заданный вопрос:{self.message_user}")
        ]
        for response_agents in list_response:
            messages.append(AIMessage(response_agents))

        final_response = get_giga_chat_manager().invoke(
            agent=agent,
            input_messages=messages,
            config=None,
            stop=None,
        )

        content = final_response.message if isinstance(final_response.message, str) else str(final_response.message)

        return (
            f"{'#' * 60}\n🎭 {agent.name}, temperature={agent.temperature}, model={agent.model}\n{'#' * 60}\n{content}\n\n"
        )
