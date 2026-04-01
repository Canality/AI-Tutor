import base64
import os
from typing import Optional, List, Dict, Any, AsyncGenerator

from utils.config import settings
from utils.logger import logger

try:
    from volcenginesdkarkruntime import Ark as RuntimeArk
except ImportError:
    RuntimeArk = None

try:
    from volcengine.ark import Ark as VolcArk
except ImportError:
    VolcArk = None


class VolcEngineClient:
    def __init__(self):
        self.access_key = settings.volc_access_key or os.getenv("ARK_API_KEY", "")
        self.secret_key = settings.volc_secret_key
        self.region = settings.volc_region
        self.endpoint = settings.volc_endpoint
        self.chat_model = settings.volc_model
        self.vision_model = settings.volc_vision_model

        self.client = None
        self.client_mode = None

        base_url = self._build_base_url(self.endpoint)

        # 优先使用方舟 runtime SDK（与官方示例一致，支持 API Key + base_url）
        if RuntimeArk and self.access_key:
            try:
                self.client = RuntimeArk(base_url=base_url, api_key=self.access_key)
                self.client_mode = "runtime"
                logger.info("Volc Engine runtime client initialized")
            except Exception as e:
                logger.error(f"Failed to init runtime ark client: {e}")

        # 回退到 volcengine.ark（AK/SK）
        if self.client is None and VolcArk and self.access_key and self.secret_key:
            try:
                self.client = VolcArk(
                    access_key_id=self.access_key,
                    secret_access_key=self.secret_key,
                    region=self.region,
                )
                self.client_mode = "volc_aksk"
                logger.info("Volc Engine AK/SK client initialized")
            except Exception as e:
                logger.error(f"Failed to init AK/SK client: {e}")

        # 再回退到 volcengine.ark（API Key）
        if self.client is None and VolcArk and self.access_key:
            try:
                self.client = VolcArk(api_key=self.access_key)
                self.client_mode = "volc_apikey"
                logger.info("Volc Engine API Key client initialized")
            except Exception as e:
                logger.error(f"Failed to init API Key client: {e}")

        if self.client is None:
            logger.warning("Volc Engine client not initialized. Please check SDK and credentials")

        if self.chat_model:
            logger.info(f"Chat model: {self.chat_model}")
        if self.vision_model:
            logger.info(f"Vision model: {self.vision_model}")

    @staticmethod
    def _build_base_url(endpoint: str) -> str:
        endpoint = (endpoint or "").strip()
        if not endpoint:
            return "https://ark.cn-beijing.volces.com/api/v3"
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            base = endpoint.rstrip("/")
        else:
            base = f"https://{endpoint.rstrip('/')}"
        if not base.endswith("/api/v3"):
            base = f"{base}/api/v3"
        return base

    def _create_chat_completion(
        self,
        params: Dict[str, Any],
        use_encrypted_header: bool = False,
    ) -> Any:
        if not self.client:
            raise RuntimeError("Volc Engine client not initialized")

        req = dict(params)
        if use_encrypted_header and self.client_mode == "runtime":
            headers = dict(req.get("extra_headers") or {})
            headers.setdefault("x-is-encrypted", "true")
            req["extra_headers"] = headers

        return self.client.chat.completions.create(**req)

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        if not self.client or not self.chat_model:
            logger.warning("Volc Engine chat model not configured")
            return None

        try:
            params: Dict[str, Any] = {
                "model": self.chat_model,
                "messages": messages,
            }
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self._create_chat_completion(params)
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            return None
        except Exception as e:
            logger.error(f"Volc Engine chat error: {e}")
            return None

    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.client or not self.chat_model:
            logger.warning("Volc Engine chat model not configured")
            return

        try:
            params: Dict[str, Any] = {
                "model": self.chat_model,
                "messages": messages,
                "stream": True,
            }
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self._create_chat_completion(params)
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
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        if not self.client or not self.vision_model:
            logger.warning("Volc Engine vision model not configured")
            return None

        try:
            if messages:
                logger.info("使用自定义 messages 进行图片分析")
                req_messages = messages
            else:
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

                req_messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ]

            params: Dict[str, Any] = {
                "model": self.vision_model,
                "messages": req_messages,
            }
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # 仅在非远程 URL 图像场景下启用加密头，避免 runtime SDK 警告
            use_encrypted_header = True
            for msg in req_messages:
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") != "image_url":
                        continue
                    image_url = item.get("image_url", {})
                    url = image_url.get("url") if isinstance(image_url, dict) else None
                    if isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
                        use_encrypted_header = False
                        break
                if not use_encrypted_header:
                    break

            response = self._create_chat_completion(params, use_encrypted_header=use_encrypted_header)
            if response and response.choices and len(response.choices) > 0:
                logger.info("图片分析成功")
                return response.choices[0].message.content

            logger.warning("图片分析返回空结果")
            return None
        except Exception as e:
            logger.error(f"Volc Engine image analysis error: {e}")
            return None


volc_client = VolcEngineClient()
