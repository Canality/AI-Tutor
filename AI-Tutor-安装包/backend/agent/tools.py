from typing import List, Dict, Any
from langchain.tools import Tool, tool
from rag.retriever import KnowledgeRetriever
from utils.logger import logger


@tool
def search_knowledge(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """搜索相关的数列知识点。

    Args:
        query: 搜索关键词
        top_k: 返回结果数量

    Returns:
        相关知识点列表
    """
    try:
        retriever = KnowledgeRetriever()
        results = retriever.search_knowledge(query, top_k)
        return results
    except Exception as e:
        logger.error(f"Search knowledge failed: {e}")
        return []



@tool
def search_examples(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """搜索相关的数列例题。

    Args:
        query: 搜索关键词
        top_k: 返回结果数量

    Returns:
        相关例题列表
    """
    try:
        retriever = KnowledgeRetriever()
        results = retriever.search_examples(query, top_k)
        logger.info(f"Search examples: {results}")
        return results
    except Exception as e:
        logger.error(f"Search examples failed: {e}")
        return []


def get_tools() -> List[Tool]:
    return [search_knowledge, search_examples]
