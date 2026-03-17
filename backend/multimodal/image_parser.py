from typing import Dict, Any, Optional
import base64
import os

from agent.prompt import VISION_ANALYSIS_PROMPT
from utils.config import settings
from utils.logger import logger
from utils.volc_engine import volc_client


class ImageParser:
    def __init__(self):
        pass
    
    async def parse_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image path {image_path} does not exist")
                return None
            
            logger.info(f"Parsing image {image_path}")

            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            prompt = VISION_ANALYSIS_PROMPT.format(image_data)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                        
                    ]

                }
            ]

            response = await volc_client.analyze_image(messages=messages)

            if not response:
                logger.error(f"Failed to parse image {image_path}")
                return None

            if response:
                logger.info("图片解析成功")
                return {
                    "success": True,
                    "question_text": response,
                    "has_question": True
                }
        except Exception as e:
            logger.error(e)
            return None


image_parser = ImageParser()
            