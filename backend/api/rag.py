"""
RAG系统API接口
提供检索和RAG Pipeline的HTTP接口
"""

import sys
import os

# 添加backend目录到路径，确保可以导入rag模块
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from rag.pipeline import rag_pipeline, RetrievedDocument
from rag.retriever import KnowledgeRetriever
from utils.logger import logger

router = APIRouter(prefix="/rag", tags=["RAG系统"])


# ============ 数据模型 ============

class SearchRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    search_type: str = Field(default="mixed", description="检索类型: knowledge/example/mixed")


class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float
    doc_type: str


class SearchResponse(BaseModel):
    success: bool
    query: str
    results: List[SearchResult]
    total: int


class RAGRequest(BaseModel):
    query: str = Field(..., description="用户问题")
    chat_history: Optional[List[Dict[str, str]]] = Field(default=None, description="历史对话")
    top_k: int = Field(default=5, ge=1, le=10, description="检索文档数量")


class RAGResponse(BaseModel):
    success: bool
    query: str
    prompt: str
    retrieved_documents: List[SearchResult]
    total_docs: int


class DocumentInfo(BaseModel):
    question_id: str
    source: str
    doc_type: str
    difficulty: Optional[int] = None
    knowledge_points: List[str] = []


class CollectionStats(BaseModel):
    name: str
    count: int


class StatsResponse(BaseModel):
    success: bool
    collections: List[CollectionStats]


# ============ API端点 ============

@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    检索相关文档
    
    支持检索知识点和例题
    """
    try:
        logger.info(f"RAG搜索请求: {request.query}")
        
        retriever = KnowledgeRetriever()
        results = []
        
        if request.search_type in ("knowledge", "mixed"):
            knowledge_results = retriever.search_knowledge(request.query, top_k=request.top_k)
            for r in knowledge_results:
                results.append(SearchResult(
                    content=r.get('content', ''),
                    metadata=r.get('metadata', {}),
                    score=1.0 - r.get('distance', 0),
                    doc_type='knowledge'
                ))
        
        if request.search_type in ("example", "mixed"):
            example_results = retriever.search_examples(request.query, top_k=request.top_k)
            for r in example_results:
                results.append(SearchResult(
                    content=r.get('content', ''),
                    metadata=r.get('metadata', {}),
                    score=1.0 - r.get('distance', 0),
                    doc_type='example'
                ))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=results[:request.top_k],
            total=len(results)
        )
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-prompt", response_model=RAGResponse)
async def generate_rag_prompt(request: RAGRequest):
    """
    生成RAG增强的提示词
    
    完整的RAG流程：检索 -> 重排序 -> 构建提示词
    """
    try:
        logger.info(f"RAG生成提示词请求: {request.query}")
        
        # 使用RAG Pipeline
        prompt, retrieved_docs = rag_pipeline.retrieve_and_build_prompt(
            query=request.query,
            chat_history=request.chat_history,
            top_k=request.top_k
        )
        
        # 转换文档格式
        doc_results = [
            SearchResult(
                content=doc.content,
                metadata=doc.metadata,
                score=doc.score,
                doc_type=doc.doc_type
            )
            for doc in retrieved_docs
        ]
        
        return RAGResponse(
            success=True,
            query=request.query,
            prompt=prompt,
            retrieved_documents=doc_results,
            total_docs=len(retrieved_docs)
        )
        
    except Exception as e:
        logger.error(f"生成提示词失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    获取RAG系统统计信息
    """
    try:
        retriever = KnowledgeRetriever()
        
        collections = [
            CollectionStats(
                name="knowledge_points",
                count=retriever.knowledge_collection.count()
            ),
            CollectionStats(
                name="example_questions",
                count=retriever.examples_collection.count()
            )
        ]
        
        return StatsResponse(
            success=True,
            collections=collections
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{doc_type}/{doc_id}")
async def get_document(doc_type: str, doc_id: str):
    """
    获取特定文档详情
    
    - doc_type: knowledge 或 example
    - doc_id: 文档ID（question_id）
    """
    try:
        retriever = KnowledgeRetriever()
        
        if doc_type == "knowledge":
            collection = retriever.knowledge_collection
        elif doc_type == "example":
            collection = retriever.examples_collection
        else:
            raise HTTPException(status_code=400, detail="无效的文档类型")
        
        # 通过metadata过滤查询
        results = collection.get(
            where={"question_id": doc_id}
        )
        
        if not results or not results.get('documents'):
            raise HTTPException(status_code=404, detail="文档未找到")
        
        return {
            "success": True,
            "doc_type": doc_type,
            "doc_id": doc_id,
            "content": results['documents'][0],
            "metadata": results['metadatas'][0] if results.get('metadatas') else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
