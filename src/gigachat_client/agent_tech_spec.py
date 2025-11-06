import logging
from typing import List, Dict, Any, override

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from sqlalchemy import false

from src.config.constants import (
    TAG,
    TAG_HELLO_PROMPT,
    TAG_SYSTEM_PROMPT,
    AgentType,
    GigaChatModel,
)

logger = logging.getLogger(__name__)

from src.gigachat_client.base_agent import AgentBase


class TechnicalSpecificationAgent(AgentBase):
    TAG_PROACTIVE_FINISH = "<proactive_finish>"
    TAG_NAGGING_AGENT_FINISH = "<nagging_agent_finish>"
    TAG_QUESTION_ASKER_FINISH = "<question_asker_finish>"

    def __init__(self):
        super().__init__(
            id_agent="tech_spec",
            name="TechnicalSpecificationAgent",
            agent_type=AgentType.BASIC,
            temperature=0.7,
            model=GigaChatModel.GIGACHAT_2,
            system_prompt="Ты координатор многоагентной системы для формирования ТЗ.",
            tools_ids=[],
            max_context_messages=30,
            max_tokens=20000,
            metadata={"predefined": True, "role": "technical_specification", "version": "1.0"}
        )
        self._proactive_agent: _ProactiveTechnicalAgent = _ProactiveTechnicalAgent()
        self._nagging_agent: _NaggingAgent = _NaggingAgent()
        self._question_asker_agent: _QuestionAskerAgent = _QuestionAskerAgent()
        self._technical_specification_agent: _TechnicalSpecificationAgent = _TechnicalSpecificationAgent()

        self._is_proactive_finish: bool = False
        self.response_nagging: str = ""
        self._is_question_asker_finish: bool = False

    @override
    def build_messages(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> BaseMessage:

        if not question:
            return self._proactive_agent.build_messages(
                question=question,
                history=history,
            )
        if not history:
            history = []
        if not additionally:
            additionally = {}

        logger.info(f"build_messages = {question}")
        logger.info(f"[Orchestrator] Current stage analysis. History length: {len(history)}")

        if not self._is_proactive_finish:
            logger.info("[Orchestrator] → Stage 1: Running ProactiveTechnicalAgent")
            proactive_response = self._proactive_agent.build_messages(
                question=question,
                history=history,
            )

            if self.TAG_PROACTIVE_FINISH.lower() not in proactive_response.content.lower():
                logger.debug(f"[Orchestrator] Stage 1 in progress: {proactive_response.content[:10]}...")
                return proactive_response
            else:
                logger.info(f"[Orchestrator] Stage 1 completed, proactive_response = {proactive_response.content}")
                self._is_proactive_finish = True

        if not self.response_nagging:
            logger.info("[Orchestrator] → Stage 2: Running NaggingAgent")
            response = self._nagging_agent.build_messages(
                question="На основе информации сформируй детальный список вопросов",
                history=history,
            )
            self.response_nagging = response.content
            logger.info(f"[Orchestrator] NaggingAgent response length: {len(self.response_nagging)}")

        if not self._is_question_asker_finish:
            logger.info("[Orchestrator] → Stage 3: Running QuestionAskerAgent (iterative)")
            additionally_updated = {
                self.TAG_NAGGING_AGENT_FINISH: self.response_nagging
            }
            additionally_updated.update(additionally)
            response = self._question_asker_agent.build_messages(
                question=question,
                history=history,
                additionally=additionally_updated
            )
            if self.TAG_QUESTION_ASKER_FINISH.lower() not in response.content.lower():
                return response
            else:
                logger.info(f"[Orchestrator] Stage 3 completed, response = {response.content}")
                self._is_question_asker_finish = True

        self._is_proactive_finish = False
        self.response_nagging = ""
        self._is_question_asker_finish = False
        logger.info("[Orchestrator] ✓ All stages completed")
        return self._technical_specification_agent.build_messages(question, history, additionally)


class _ProactiveTechnicalAgent(AgentBase):

    def __init__(self):
        super().__init__(
            id_agent="PreviewProactiveAgent",
            name="PreviewProactiveAgent",
            agent_type=AgentType.BASIC,
            temperature=0.8,
            model=GigaChatModel.GIGACHAT_2_MAX,
            system_prompt=(
                "Ты — принимаешь данные для разработки технического задания абсолютно любой жизненной ситуации."
                "Твоя задача — получить первичную вводную информацию от пользователя, в каком направлении задача."
                f"Когда будет понятна цель пользователя отправляй тег {TechnicalSpecificationAgent.TAG_PROACTIVE_FINISH} "
                f"Не задавай много вопросов "
                f" МАКСИМУМ 3 ВОАРОСА"
                "1 Ты должен ЗАДАТЬ ВОПРОС для уточнения: "
                "2 Получить ответ "
                "3 ЗАДАТЬ ВОПРОС еще вопрос для уточнения: "
                "4 Получить ответ "
                "- не использовать длинных вступлений или пояснений."

                f"После того как оба ответа получены, ты должен в следующем сообщении отправить **только тег {TechnicalSpecificationAgent.TAG_PROACTIVE_FINISH}**, без каких-либо дополнительных комментариев, текста или знаков препинания."

                "ПРИМЕР ВЗАИМОДЕЙСТВИЯ:"
                "Пользователь: ..."
                "Агент: ...?"
                "Пользователь: ..."
                "Агент: ...?"
                "Пользователь: ..."
                f"Агент: {TechnicalSpecificationAgent.TAG_PROACTIVE_FINISH}"
            ),
            hello_prompt=HumanMessage(
                "Поздоровайся и предложи составить ТЗ по желаниям пользователя"
            ),
            tools_ids=[],
            max_context_messages=40,
            max_tokens=20000,
            metadata={"predefined": True, "role": "technical specification", "version": "1.0"}
        )


class _NaggingAgent(AgentBase):

    def __init__(self):
        super().__init__(
            id_agent="NaggingAgent",
            name="NaggingAgent",
            agent_type=AgentType.BASIC,
            temperature=0.5,
            model=GigaChatModel.GIGACHAT_2_MAX,
            system_prompt=(
                "Ты — аналитик по сбору требований под любую задачу. "
                "На основе вводных данных пользователя создай необходимое количество уточняющих вопросов, "
                "НЕ МЕНЕЕ 1 И НЕ БОЛЕЕ 5 ВОПРОСОВ, которые помогут подготовить полное техническое задание."
                "Формулируй вопросы конкретно, без лишних объяснений и комментариев."
                "Старайся охватить цели, аудиторию, платформу, функционал, визуальные и технические детали."
                "МАКСИМУМ 5 ВОПРОСОВ\n\n"
                "ПРИМЕР ВХОДНЫХ ДАННЫХ:"
                "..."
                "ПРИМЕР ОТВЕТА:"
                "1. ...?"
                "2. ...?"
                "3. ...?"
                "4. ..."
                "5. ...\n\n"
            ),
            hello_prompt=None,
            tools_ids=[],
            max_context_messages=40,
            max_tokens=20000,
            metadata={"predefined": True, "role": "technical specification", "version": "1.0"}
        )


class _QuestionAskerAgent(AgentBase):

    def __init__(self):
        super().__init__(
            id_agent="_QuestionAskerAgent",
            name="_QuestionAskerAgent",
            agent_type=AgentType.BASIC,
            temperature=0.3,
            model=GigaChatModel.GIGACHAT_2,
            system_prompt=(
                "Ты — агент, который задает пользователю список вопросов для уточнения требований к проекту."
                "Твоя задача:"
                "1. Получить список вопросов, который тебе предоставили."
                "2. Задавать их пользователю **по одному сообщению за раз**."
                f"3. После получения ответа на **последний вопрос** отправить **только тег {TechnicalSpecificationAgent.TAG_QUESTION_ASKER_FINISH}**."
                "4. Никаких дополнительных комментариев, пояснений или текста рядом с тегом быть не должно."
                "5. Не менять формулировку вопросов, не сокращать их.\n\n"
                "ПРИМЕР ВЗАИМОДЕЙСТВИЯ:"
                "Список вопросов:"
                "1. ...?"
                "2. ...?"
                "3. ...?"
                "Агент задает:"
                "Агент: 1. ...?"
                "Пользователь: ..."
                "Агент: 2. ...?"
                "Пользователь: ..."
                "Агент: 3. ...?"
                "Пользователь: ..."
                f"Агент: {TechnicalSpecificationAgent.TAG_QUESTION_ASKER_FINISH}"
            ),
            hello_prompt=None,
            tools_ids=[],
            max_context_messages=30,
            max_tokens=20000,
            metadata={"predefined": True, "role": "technical specification", "version": "1.0"}
        )

    @override
    def build_messages(
            self,
            question: str = "",
            history: List[Dict[str, str]] = None,
            additionally: Dict[str, str] = None
    ) -> BaseMessage:
        if not additionally:
            additionally = {}

        nagging_content = additionally.get(TechnicalSpecificationAgent.TAG_NAGGING_AGENT_FINISH, "")
        messages: List[Any] = [
            SystemMessage(
                content=f"{self.system_prompt}\n\n Список Вопросов\n{nagging_content}",
                kwargs={TAG, TAG_SYSTEM_PROMPT}
            ),
        ]

        recent_messages: List[Any] = []
        num_messages = min(len(history), self.max_context_messages)
        for msg in history[-num_messages:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            tag = msg.get("tag", "")

            if tag in (TAG_SYSTEM_PROMPT, TAG_HELLO_PROMPT):
                continue

            elif role == "user":
                recent_messages.append(HumanMessage(content=content))
            elif role == "agent":
                recent_messages.append(AIMessage(content=content))

        messages.extend(recent_messages)

        messages.append(HumanMessage(content=question))
        return self._llm.invoke(messages)


class _TechnicalSpecificationAgent(AgentBase):

    def __init__(self):
        super().__init__(
            id_agent="TechnicalSpecificationAgent",
            name="Agent Technical Specification",
            agent_type=AgentType.BASIC,
            temperature=1.3,
            model=GigaChatModel.GIGACHAT_2_MAX,
            system_prompt=(
                "Ты — эксперт по написанию технических заданий. "
                "Используй исходные данные и уточнённые ответы пользователя, "
                "чтобы составить полное, структурированное и понятное ТЗ. "
                "Не добавляй ничего от себя, оформи красиво в виде документа."
            ),
            hello_prompt=None,
            tools_ids=[],
            max_context_messages=70,
            max_tokens=40000,
            metadata={"predefined": True, "role": "technical specification", "version": "1.0"}
        )
