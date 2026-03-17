import base64
import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from utils.config import settings
from utils.logger import logger

try:
    from volcengine.ark import Ark
except ImportError:
    logger.warning("volcengine SDK not installed. Install it with: pip install volcengine")
    Ark = None


class VolcEngineClient:
    def __init__(self):
        self.access_key = settings.volc_access_key
        self.secret_key = settings.volc_secret_key
        self.region = settings.volc_region
        self.endpoint = settings.volc_endpoint
        self.chat_model = settings.volc_model
        self.vision_model = settings.volc_vision_model
        self.client = None

        if Ark and self.access_key and self.secret_key:
            try:
                self.client = Ark(
                    access_key_id=self.access_key,
                    secret_access_key=self.secret_key,
                    region=self.region
                )
                logger.info("Volc Engine client initialized successfully")
                if self.chat_model:
                    logger.info(f"Chat model: {self.chat_model}")
                if self.vision_model:
                    logger.info(f"Vision model: {self.vision_model}")
            except Exception as e:
                logger.error(f"Failed to initialize Volc Engine client: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """使用文字模型进行对话。
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            模型回复
        """
        if not self.client or not self.chat_model:
            logger.warning("Volc Engine chat model not configured")
            return None

        try:
            params = {
                "model": self.chat_model,
                "messages": messages
            }

            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)

            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content

            return None

        except Exception as e:
            logger.error(f"Volc Engine chat error: {e}")
            return None

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """使用文字模型进行流式对话。
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            模型回复片段
        """
        if not self.client or not self.chat_model:
            logger.warning("Volc Engine chat model not configured")
            return

        try:
            params = {
                "model": self.chat_model,
                "messages": messages,
                "stream": True
            }

            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)

            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content

        except Exception as e:
            logger.error(f"Volc Engine stream chat error: {e}")

    async def analyze_image(
        self,
        image_path: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        messages: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """使用视觉模型分析图片。
        
        Args:
            image_path: 图片文件路径（可选）
            prompt: 提示词（可选）
            temperature: 温度参数
            max_tokens: 最大token数
            messages: 完整的消息列表（可选，优先使用）
            
        Returns:
            分析结果
        """
        if not self.client or not self.vision_model:
            logger.warning("Volc Engine vision model not configured")
            return None

        try:
            # 如果提供了 messages，直接使用
            if messages:
                logger.info("使用自定义 messages 进行图片分析")
                params = {
                    "model": self.vision_model,
                    "messages": messages
                }
            else:
                # 传统方式：通过 image_path 加载图片
                if not image_path:
                    logger.error("Either image_path or messages must be provided")
                    return None
                
                if not os.path.exists(image_path):
                    logger.error(f"Image file not found: {image_path}")
                    return None

                logger.info(f"开始分析图片: {image_path}")

                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()

                if prompt is None:
                    prompt = "请分析这张图片中的数学数列题目，提取题目文本内容。"

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
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

                params = {
                    "model": self.vision_model,
                    "messages": messages
                }

            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)

            if response and response.choices and len(response.choices) > 0:
                logger.info("图片分析成功")
                return response.choices[0].message.content

            logger.warning("图片分析返回空结果")
            return None

        except Exception as e:
            logger.error(f"Volc Engine image analysis error: {e}")
            return None


volc_client = VolcEngineClient()
