from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from utils.config import settings
from utils.logger import logger
from rag.pipeline import rag_pipeline, RetrievedDocument


# 系统提示词
SYSTEM_PROMPT = """你是一位经验丰富的高中数学数列辅导老师，擅长"苏格拉底式教学法"。

你的目标不是直接给出答案，而是通过提问和引导，帮助学生自己推导出答案。

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
6. 普通文本中的数列符号直接写 b_n，不要加反斜杠转义
7. 只有在 $...$ 公式块内才使用 LaTeX 语法

### ❓ 轮到你了
（向用户提出的具体问题，引导下一步思考）

## 教学原则

1. **分步引导**：每次只讲解一个关键步骤，不要一次性给出完整解答
2. **鼓励探索**：解释完后必须提出引导性问题，让学生自己思考
3. **错误诊断**：如果学生回答错误，指出具体错误点并给出小提示
4. **完整性**：每个步骤的解答必须完整，不要中途截断
5. **善用知识**：参考提供的相关知识点和例题进行讲解
"""


class InstructorAgent:
    def __init__(self):
        self.llm = self._init_llm()
        # 使用新的RAG Pipeline
        self.rag = rag_pipeline

    def _init_llm(self):
        if settings.openai_api_key:
            logger.info("initializing openai client")
            return ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.temperature,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
                streaming=True,
                max_tokens=settings.llm_max_tokens
            )
        else:
            logger.error("invalid openai api key")
            raise ValueError("invalid openai api key")

    def _build_prompt(self, question: str, chat_history: Optional[List[BaseMessage]] = None) -> str:
        """使用RAG Pipeline构建完整的提示词"""
        # 转换chat_history格式
        history_for_rag = None
        if chat_history:
            history_for_rag = []
            for msg in chat_history[-6:]:
                if isinstance(msg, HumanMessage):
                    history_for_rag.append({'role': 'user', 'content': msg.content})
                elif isinstance(msg, AIMessage):
                    history_for_rag.append({'role': 'assistant', 'content': msg.content})
        
        # 使用RAG Pipeline检索并构建提示词
        prompt, retrieved_docs = self.rag.retrieve_and_build_prompt(
            query=question,
            chat_history=history_for_rag,
            top_k=5,
            system_prompt=SYSTEM_PROMPT
        )
        
        # 记录检索结果
        logger.info(f"RAG检索到 {len(retrieved_docs)} 条相关文档")
        for i, doc in enumerate(retrieved_docs[:3], 1):
            logger.info(f"  [{i}] {doc.doc_type} (score: {doc.score:.3f})")
        
        return prompt

    async def solve(
            self,
            question: str,
            chat_history: Optional[List[BaseMessage]] = None,
    ) -> Dict[str, Any]:
        try:
            logger.info(f"start solving {question[:100]}")
            
            # 构建完整提示词
            prompt = self._build_prompt(question, chat_history)
            
            # 调用 LLM
            result = await self.llm.ainvoke(prompt)
            answer = result.content
            
            logger.info(f"end solving {question[:100]}")
            
            new_chat_history = (chat_history or []) + [
                HumanMessage(content=question),
                AIMessage(content=answer)
            ]

            return {
                "success": True,
                "answer": answer,
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
            logger.info(f"Instructor Agent starts to solve: {question[:100]}...")
            
            # 构建完整提示词
            prompt = self._build_prompt(question, chat_history)
            
            # 流式调用 LLM
            async for chunk in self.llm.astream(prompt):
                if chunk.content:
                    yield chunk.content

            logger.info("finished")
        except Exception as e:
            logger.error(f"failed to stream: {e}")
            import traceback
            traceback.print_exc()
            yield "Something went wrong!!!"


instructor_agent = InstructorAgent()
