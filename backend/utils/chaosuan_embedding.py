"""超算互联网Embedding模型客户端

使用超算互联网API调用Qwen3-Embedding-8B模型
文档: https://www.scnet.cn/
"""
import asyncio
from typing import List, Optional
import aiohttp
from utils.config import settings
from utils.logger import logger


class ChaoSuanEmbeddingClient:
    """超算互联网Embedding客户端"""
    
    def __init__(self):
        self.api_key = settings.chaosuan_api_key
        self.api_base = settings.chaosuan_api_base or "https://api.scnet.cn/v1"
        self.model = settings.chaosuan_embedding_model or "Qwen3-Embedding-8B"
        
        if not self.api_key:
            logger.warning("超算互联网API key未配置")
        else:
            logger.info(f"超算互联网Embedding客户端初始化完成，模型: {self.model}")
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """对单个文本进行向量化"""
        result = await self.embed_texts([text])
        if result and len(result) > 0:
            return result[0]
        return None
    
    async def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """对多个文本进行向量化"""
        if not self.api_key:
            logger.error("超算互联网API key未配置")
            return None
        
        if not texts:
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "input": texts
            }
            
            url = f"{self.api_base}/embeddings"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        embeddings = []
                        for item in data.get("data", []):
                            embedding = item.get("embedding", [])
                            embeddings.append(embedding)
                        logger.info(f"成功获取{len(embeddings)}个文本的向量表示")
                        return embeddings
                    else:
                        error_text = await response.text()
                        logger.error(f"超算互联网API调用失败: {response.status}, {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"超算互联网Embedding调用失败: {e}")
            return None


# 全局客户端实例
chaosuan_embedding_client = ChaoSuanEmbeddingClient()


async def test_embedding():
    """测试embedding功能"""
    client = ChaoSuanEmbeddingClient()
    texts = ["等差数列的通项公式是什么？", "等比数列求和公式"]
    result = await client.embed_texts(texts)
    if result:
        print(f"成功获取{len(result)}个向量")
        print(f"向量维度: {len(result[0])}")
    else:
        print("获取向量失败")


if __name__ == "__main__":
    asyncio.run(test_embedding())
