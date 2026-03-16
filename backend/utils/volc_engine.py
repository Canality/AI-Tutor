import json
from typing import Optional, List, Dict, Any
from backend.utils.config import settings
from backend.utils.logger import logger

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
        self.model = settings.volc_model
        self.client = None

        if Ark and self.access_key and self.secret_key:
            try:
                self.client = Ark(
                    access_key_id=self.access_key,
                    secret_access_key=self.secret_key,
                    region=self.region
                )
                logger.info("Volc Engine client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Volc Engine client: {e}")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        if not self.client or not self.model:
            logger.warning("Volc Engine client not configured")
            return None

        try:
            params = {
                "model": self.model,
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
    ):
        if not self.client or not self.model:
            logger.warning("Volc Engine client not configured")
            return

        try:
            params = {
                "model": self.model,
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


volc_client = VolcEngineClient()
