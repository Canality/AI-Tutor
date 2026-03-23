"""硅基流动视觉模型客户端"""
import base64
import os
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI
from utils.config import settings
from utils.logger import logger


class SiliconFlowVisionClient:
    """硅基流动视觉模型客户端（OpenAI 兼容格式）"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_api_base
        self.vision_model = settings.vision_model or "Qwen/Qwen2-VL-72B-Instruct"
        
        if not self.api_key:
            logger.warning("SiliconFlow API key not configured")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"SiliconFlow vision client initialized with model: {self.vision_model}")
    
    async def analyze_image(
        self,
        image_path: Optional[str] = None,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """分析图片内容"""
        if not self.client:
            logger.warning("SiliconFlow client not initialized")
            return None
        
        try:
            if messages:
                # 使用传入的 messages
                req_messages = messages
            else:
                # 从图片路径创建 messages
                if not image_path or not os.path.exists(image_path):
                    logger.error(f"Image path invalid: {image_path}")
                    return None
                
                logger.info(f"Analyzing image: {image_path}")
                
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()
                
                if prompt is None:
                    prompt = "请分析这张图片中的数学数列题目，提取题目文本内容。"
                
                req_messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            
            # 调用硅基流动 API
            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=req_messages,
                temperature=temperature or 0.7,
                max_tokens=max_tokens or 2000
            )
            
            if response and response.choices:
                content = response.choices[0].message.content
                logger.info("Image analysis successful")
                return content
            
            logger.warning("Image analysis returned empty result")
            return None
            
        except Exception as e:
            logger.error(f"SiliconFlow vision error: {e}")
            return None


# 全局客户端实例
siliconflow_vision_client = SiliconFlowVisionClient()
