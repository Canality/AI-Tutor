from typing import Dict, Any, Optional
import base64
import os

from utils.config import settings
from utils.logger import logger
from utils.siliconflow_vision import siliconflow_vision_client


# 图片分析提示词
VISION_ANALYSIS_PROMPT = """请仔细分析这张图片中的数学数列题目。

任务要求：
1. 识别图片中的数学公式、文字和符号
2. 提取完整的题目内容（包括已知条件、求解目标）
3. 如果图片包含解题过程，分析其解题思路

输出格式要求：
请以纯文本形式返回题目内容，不要添加JSON格式或其他格式标记。只需返回提取到的题目文本即可。

示例输出格式：
已知数列{a_n}满足a_1=1，a_{n+1}=2a_n+1，求数列{a_n}的通项公式。

如果图片中没有数学题目，请回复："图片中未识别到数学题目"
"""


class ImageParser:
    def __init__(self):
        pass
    
    async def parse_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image path {image_path} does not exist")
                return None
            
            logger.info(f"Parsing image {image_path}")

            # 读取图片并编码为base64
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                image_data = base64.b64encode(image_bytes).decode()
                logger.info(f"Image base64 encoded, length: {len(image_data)} chars")

            # 检测图片格式
            image_format = self._detect_image_format(image_bytes)
            logger.info(f"Detected image format: {image_format}")

            # 构建 messages，正确的多模态格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": VISION_ANALYSIS_PROMPT,
                        }
                    ]
                }
            ]

            logger.info(f"Sending image to vision model: {settings.vision_model}")
            response = await siliconflow_vision_client.analyze_image(messages=messages)

            if not response:
                logger.error(f"Vision model returned empty response for {image_path}")
                return {
                    "success": False,
                    "question_text": "",
                    "has_question": False,
                    "error": "视觉模型返回空结果"
                }

            # 检查是否成功识别到题目
            has_question = "图片中未识别到数学题目" not in response and len(response.strip()) > 10
            
            logger.info(f"Successfully parsed image, has_question: {has_question}")
            logger.info(f"Extracted text preview: {response[:100]}...")
            
            return {
                "success": True,
                "question_text": response.strip(),
                "has_question": has_question
            }
            
        except Exception as e:
            logger.error(f"Image parsing error: {e}", exc_info=True)
            return {
                "success": False,
                "question_text": "",
                "has_question": False,
                "error": str(e)
            }
    
    def _detect_image_format(self, image_bytes: bytes) -> str:
        """检测图片格式"""
        if image_bytes.startswith(b'\x89PNG'):
            return 'png'
        elif image_bytes.startswith(b'\xff\xd8'):
            return 'jpeg'
        elif image_bytes.startswith(b'GIF89a') or image_bytes.startswith(b'GIF87a'):
            return 'gif'
        elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
            return 'webp'
        else:
            return 'jpeg'  # 默认返回jpeg


image_parser = ImageParser()
            