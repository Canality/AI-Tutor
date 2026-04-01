from typing import Dict, Any, Optional, AsyncGenerator, List

from langchain_core.messages import BaseMessage

from agent.instructor import instructor_agent
from multimodal.image_parser import image_parser
from utils.logger import logger


class TutorService:
    def __init__(self):
        pass

    async def process_question(
            self,
            text_content: str,
            image_path: Optional[str] = None,
            chat_history: Optional[List[BaseMessage]] = None,
    ):
        try:
            logger.info(f"Tutor service started for {text_content}")
            chat_history = chat_history or []
            question_text = text_content

            if image_path:
                logger.info(f"Tutor service started for {image_path}")
                parse_result = await image_parser.parse_image(image_path)

                if parse_result and parse_result.get("has_question"):
                    parsed_question = parse_result.get("question_text", "")
                    if parsed_question:
                        question_text = f"{text_content}\n\ncontent of the question：{parsed_question}"
                        logger.info("finished parsing image, start to solve question")

            logger.info(f"Tutor service started for {question_text[0:200]}")
            result = await instructor_agent.solve(question_text, chat_history)
            return result
        except Exception as e:
            logger.error(e)
            return {
                "success": False,
                "error": str(e),
                "answer": "Something went wrong, I'm sorry.",
                "chat_history": chat_history
            }

    async def process_question_stream(
        self,
        text_content: str,
        image_path: Optional[str] = None,
        chat_history: Optional[List[BaseMessage]] = None 
    ) -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Tutor service started for text: {text_content[:100]}...")
            chat_history = chat_history or []
            question_text = text_content

            if image_path:
                logger.info(f"Processing image: {image_path}")
                parse_result = await image_parser.parse_image(image_path)
                
                if parse_result:
                    logger.info(f"Image parse result: success={parse_result.get('success')}, has_question={parse_result.get('has_question')}")
                    
                    if parse_result.get("has_question"):
                        parsed_question = parse_result.get("question_text", "")
                        if parsed_question:
                            question_text = f"{text_content}\n\n【图片中的题目内容】：{parsed_question}"
                            yield "✅ 图片解析完成，正在分析题目...\n\n"
                    else:
                        # 图片解析成功但没有识别到题目
                        error_msg = parse_result.get("error", "")
                        logger.warning(f"Image parsed but no question found: {error_msg}")
                        yield "⚠️ 未能从图片中识别到数学题目，请尝试：\n"
                        yield "1. 确保图片清晰，文字可读\n"
                        yield "2. 直接输入题目文字描述\n\n"
                        # 仍然继续处理用户输入的文字
                else:
                    logger.error("Image parser returned None")
                    yield "⚠️ 图片解析失败，将仅根据您输入的文字进行回答...\n\n"

            logger.info(f"Final question text: {question_text[:200]}...")
            
            async for chunk in instructor_agent.solve_stream(question_text, chat_history):
                yield chunk

        except Exception as e:
            logger.error(f"Tutor service error: {e}", exc_info=True)
            yield f"❌ 处理出错: {str(e)}\n请稍后重试或联系管理员。"


tutor_service = TutorService()
