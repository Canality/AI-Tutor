from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from agent.prompt import INSTRUCTOR_PROMPT
from agent.tools import get_tools
from utils.config import settings
from utils.logger import logger
from utils.volc_engine import volc_client


class InstructorAgent:
    def __init__(self):
        self.tools = get_tools()
        self.llm = self._init_llm()
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=INSTRUCTOR_PROMPT,
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=settings.verbose,
            handle_parsing_errors=True,
            max_iterations=12,
            max_execution_time=90,
            early_stopping_method="generate",
            return_intermediate_steps=False
        )


    def _init_llm(self):
        if settings.volc_access_key and settings.volc_model:
            logger.info("initializing volc client")
            return ChatOpenAI(
                model=settings.volc_model,
                temperature=settings.temperature,
                api_key=settings.volc_access_key,
                base_url=f"https://{settings.volc_endpoint}/api/v3",
                streaming=True,
                # max_tokens=settings.max_tokens
            )
        elif settings.openai_api_key:
            logger.info("initializing openai client")
            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.temperature,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
                streaming=True,
                max_tokens=settings.max_tokens
            )
        else:
            logger.error("invalid openai api key")
            raise ValueError("invalid openai api key")

    async def solve(
            self,
            question: str,
            chat_history: Optional[List[BaseMessage]] = None,
    ) -> Dict[str, Any]:

        try:
            chat_history = chat_history or []
            logger.info(f"start solving {question[:100]}")
            result = await self.agent_executor.ainvoke(
                {
                    "input": question,
                    "chat_history": chat_history
                }
            )
            logger.info(f"end solving {question[:100]}")
            new_chat_history = chat_history + [
                HumanMessage(content=question),
                AIMessage(content=result["output"])
            ]

            return {
                "success": True,
                "answer": result["output"],
                "chat_history": new_chat_history
            }
        except Exception as e:
            logger.error(f"failed to solve {e}")
            return {"success": False,
                    "error": str(e),
                    "answer": "something went wrong!!!"}

    async def solve_stream(
            self,
            question: str,
            chat_history: Optional[List[BaseMessage]] = None
    ) -> AsyncGenerator[str, None]:

        try:
            chat_history = chat_history or []
            logger.info(f"Instructor Agent starts to solve: {question[:100]}...")

            async for event in self.agent_executor.astream_events(
                {
                        "input": question,
                        "chat_history": chat_history
                    },
                    version="v1"
            ):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    yield f"\n[useing tools] {tool_name}\n"


            logger.info("finished")
        except Exception as e:
            logger.error(f"failed to stream: {e}")
            yield "Something went wrong!!!"


instructor_agent = InstructorAgent()
