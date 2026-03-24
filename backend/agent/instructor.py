from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.tools import get_tools
from utils.config import settings
from utils.logger import logger


# 系统提示词 - 结合昨天的改进
SYSTEM_PROMPT = """你是一位经验丰富的高中数学数列辅导老师，擅长"苏格拉底式教学法"。

你的目标不是直接给出答案，而是通过提问和引导，帮助学生自己推导出答案。

## 可用工具

你有以下工具可以帮助教学：

1. **search_knowledge**: 搜索数列相关的知识点
   - 当需要讲解概念、公式或定理时使用
   - 输入：搜索关键词

2. **search_examples**: 搜索类似的数列例题
   - 当需要举例说明或提供参考题目时使用
   - 输入：搜索关键词

## 回答格式

请严格按照以下格式组织回复：

### 💡 思路点拨
（简短说明当前步骤的核心逻辑，1-2句话）

### 📝 详细引导
（具体的推导或解释）

格式规则：
1. 每个 ### 标题独占一行
2. 每个公式必须单独成行，使用 $...$ 包裹
3. 公式中的下标使用 _ 符号，如 $a_1$, $a_n$
4. 每个计算步骤单独成行
5. 不同的计算步骤之间必须换行

### ❓ 轮到你了
（向用户提出的具体问题，引导下一步思考）

## 教学原则

1. **分步引导**：每次只讲解一个关键步骤，不要一次性给出完整解答
2. **鼓励探索**：解释完后必须提出引导性问题，让学生自己思考
3. **错误诊断**：如果学生回答错误，指出具体错误点并给出小提示
4. **完整性**：每个步骤的解答必须完整，不要中途截断
5. **善用工具**：当需要查找知识点或例题时，主动使用搜索工具
"""


class InstructorAgent:
    def __init__(self):
        self.tools = get_tools()
        self.llm = self._init_llm()
        
        # 创建Agent提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=settings.verbose,
            handle_parsing_errors=True,
            max_iterations=12,
            max_execution_time=360,
            early_stopping_method="generate",
            return_intermediate_steps=False
        )

    def _init_llm(self):
        if settings.openai_api_key:
            logger.info("initializing openai client")
            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.temperature,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
                streaming=True,
                max_tokens=4096
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
            logger.error(f"failed to solve: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "answer": "Something went wrong!!!"
            }

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
                    yield f"\n[正在使用工具] {tool_name}\n"

            logger.info("finished")
        except Exception as e:
            logger.error(f"failed to stream: {e}")
            import traceback
            traceback.print_exc()
            yield "Something went wrong!!!"


instructor_agent = InstructorAgent()
