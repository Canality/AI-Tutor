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
                        yield "I've parsed the question, now I'm going to solve it.\n\n"

            async for chunk in instructor_agent.solve_stream(question_text, chat_history):
                yield chunk

        except Exception as e:
            logger.error(e)
            yield "Something went wrong"


tutor_service = TutorService()
