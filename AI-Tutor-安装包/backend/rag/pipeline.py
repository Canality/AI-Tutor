"""
RAG系统核心模块 - 增强检索与生成

提供完整的RAG Pipeline：
1. 多路召回（向量检索 + 关键词检索）
2. 重排序（Reranking）
3. 上下文压缩
4. 提示词组装
5. 答案生成
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from rag.retriever import KnowledgeRetriever
from utils.logger import logger


@dataclass
class RetrievedDocument:
    """检索到的文档"""
    content: str
    metadata: Dict[str, Any]
    score: float  # 相似度分数
    doc_type: str  # 'knowledge' 或 'example'
    
    def to_context(self) -> str:
        """转换为上下文格式"""
        return f"[{self.doc_type.upper()}] {self.content}"


class RAGPipeline:
    """
    RAG Pipeline - 完整的检索增强生成流程
    
    流程：
    1. 查询理解与分析
    2. 多路召回（向量检索 + 关键词匹配）
    3. 重排序
    4. 上下文压缩与组装
    5. 生成增强提示词
    """
    
    def __init__(self):
        self.retriever = KnowledgeRetriever()
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        分析查询，提取关键信息
        
        Returns:
            {
                'query_type': 'knowledge' | 'example' | 'mixed',
                'key_concepts': List[str],
                'difficulty_hint': Optional[int],
                'clean_query': str
            }
        """
        result = {
            'query_type': 'mixed',
            'key_concepts': [],
            'difficulty_hint': None,
            'clean_query': query.strip()
        }
        
        # 提取难度提示
        difficulty_patterns = [
            r'(\d+)\s*分',
            r'难度\s*(\d+)',
            r'第?([12345])\s*星',
        ]
        for pattern in difficulty_patterns:
            match = re.search(pattern, query)
            if match:
                result['difficulty_hint'] = int(match.group(1))
                break
        
        # 识别查询类型
        knowledge_keywords = ['什么是', '定义', '公式', '概念', '原理', '定理']
        example_keywords = ['例题', '例子', '怎么解', '怎么做', '求解', '证明']
        
        has_knowledge = any(kw in query for kw in knowledge_keywords)
        has_example = any(kw in query for kw in example_keywords)
        
        if has_knowledge and not has_example:
            result['query_type'] = 'knowledge'
        elif has_example and not has_knowledge:
            result['query_type'] = 'example'
        else:
            result['query_type'] = 'mixed'
        
        # 提取关键概念（简单实现，可扩展为NER）
        # 数列相关概念
        sequence_concepts = [
            '等差数列', '等比数列', '递推数列', '数列求和',
            '裂项放缩', '数学归纳法', '通项公式', '前n项和',
            '放缩法', '不等式证明', '单调性', '有界性'
        ]
        
        for concept in sequence_concepts:
            if concept in query:
                result['key_concepts'].append(concept)
        
        return result
    
    def multi_way_retrieval(
        self,
        query: str,
        top_k: int = 5,
        query_analysis: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """
        多路召回检索
        
        1. 向量检索知识点
        2. 向量检索例题
        3. 关键词匹配补充
        """
        documents = []
        query_analysis = query_analysis or self.analyze_query(query)
        
        # 根据查询类型调整检索策略
        query_type = query_analysis.get('query_type', 'mixed')
        
        # 1. 向量检索知识点
        if query_type in ('knowledge', 'mixed'):
            try:
                knowledge_results = self.retriever.search_knowledge(query, top_k=top_k)
                for result in knowledge_results:
                    documents.append(RetrievedDocument(
                        content=result.get('content', ''),
                        metadata=result.get('metadata', {}),
                        score=1.0 - result.get('distance', 0),  # 距离转相似度
                        doc_type='knowledge'
                    ))
            except Exception as e:
                logger.error(f"知识点检索失败: {e}")
        
        # 2. 向量检索例题
        if query_type in ('example', 'mixed'):
            try:
                example_results = self.retriever.search_examples(query, top_k=top_k)
                for result in example_results:
                    documents.append(RetrievedDocument(
                        content=result.get('content', ''),
                        metadata=result.get('metadata', {}),
                        score=1.0 - result.get('distance', 0),
                        doc_type='example'
                    ))
            except Exception as e:
                logger.error(f"例题检索失败: {e}")
        
        # 3. 关键词匹配补充（简单实现）
        key_concepts = query_analysis.get('key_concepts', [])
        if key_concepts:
            for concept in key_concepts:
                try:
                    # 用关键概念再检索一次
                    concept_results = self.retriever.search_knowledge(concept, top_k=2)
                    for result in concept_results:
                        doc = RetrievedDocument(
                            content=result.get('content', ''),
                            metadata=result.get('metadata', {}),
                            score=(1.0 - result.get('distance', 0)) * 0.9,  # 关键词匹配稍微降权
                            doc_type='knowledge'
                        )
                        # 去重
                        if not any(d.metadata.get('question_id') == doc.metadata.get('question_id') 
                                  for d in documents if doc.metadata.get('question_id')):
                            documents.append(doc)
                except Exception as e:
                    logger.error(f"关键词检索失败: {e}")
        
        # 按分数排序
        documents.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"多路召回完成：共 {len(documents)} 条文档")
        return documents
    
    def rerank_documents(
        self,
        query: str,
        documents: List[RetrievedDocument],
        top_n: int = 5
    ) -> List[RetrievedDocument]:
        """
        重排序（简单实现，可替换为Cross-Encoder模型）
        
        排序因素：
        1. 向量相似度分数
        2. 关键词匹配度
        3. 文档类型权重
        """
        if not documents:
            return []
        
        query_words = set(query.lower().split())
        
        for doc in documents:
            # 基础分数
            base_score = doc.score
            
            # 关键词匹配加分
            content_lower = doc.content.lower()
            keyword_matches = sum(1 for word in query_words if word in content_lower)
            keyword_score = min(keyword_matches * 0.05, 0.2)  # 最多加0.2
            
            # 类型权重：例题稍微优先
            type_weight = 1.05 if doc.doc_type == 'example' else 1.0
            
            # 综合分数
            doc.score = (base_score + keyword_score) * type_weight
        
        # 重新排序
        documents.sort(key=lambda x: x.score, reverse=True)
        
        # 返回Top N
        return documents[:top_n]
    
    def compress_context(
        self,
        documents: List[RetrievedDocument],
        max_tokens: int = 1500
    ) -> str:
        """
        上下文压缩
        
        策略：
        1. 优先保留高分文档
        2. 截断过长文档
        3. 添加文档间分隔
        """
        if not documents:
            return ""
        
        # 简单估算：每个字符约0.5个token（中文）
        max_chars = int(max_tokens * 2)
        
        contexts = []
        current_chars = 0
        
        for i, doc in enumerate(documents, 1):
            # 格式化文档
            header = f"\n{'='*40}\n[相关文档 {i}] 类型: {doc.doc_type}\n{'='*40}\n"
            content = doc.content
            
            # 计算剩余空间
            remaining = max_chars - current_chars - len(header)
            
            if remaining <= 0:
                break
            
            # 截断内容
            if len(content) > remaining:
                content = content[:remaining] + "\n...[内容已截断]"
            
            contexts.append(header + content)
            current_chars += len(header) + len(content)
        
        return "\n".join(contexts)
    
    def build_rag_prompt(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        构建RAG增强的提示词
        """
        if system_prompt is None:
            system_prompt = """你是一位经验丰富的高中数学数列辅导老师，擅长"苏格拉底式教学法"。

你的目标不是直接给出答案，而是通过提问和引导，帮助学生自己推导出答案。

## 回答格式

请严格按照以下格式组织回复：

### 💡 思路点拨
（简短说明当前步骤的核心逻辑，1-2句话）

### 📝 详细引导
（具体的推导或解释）

### ❓ 轮到你了
（向用户提出的具体问题，引导下一步思考）

## 教学原则

1. **分步引导**：每次只讲解一个关键步骤，不要一次性给出完整解答
2. **鼓励探索**：解释完后必须提出引导性问题，让学生自己思考
3. **错误诊断**：如果学生回答错误，指出具体错误点并给出小提示
4. **善用知识**：参考提供的相关知识点和例题进行讲解
"""
        
        # 构建历史对话
        history_text = ""
        if chat_history:
            history_parts = []
            for msg in chat_history[-4:]:  # 只保留最近4轮
                role = msg.get('role', '')
                content = msg.get('content', '')
                if role == 'user':
                    history_parts.append(f"学生：{content}")
                elif role == 'assistant':
                    history_parts.append(f"老师：{content}")
            if history_parts:
                history_text = "\n\n".join(history_parts) + "\n\n"
        
        # 组装完整提示词
        prompt = f"""{system_prompt}

{'='*60}
相关参考资料（请基于这些资料进行讲解）：
{'='*60}
{context if context else "（暂无相关参考资料）"}
{'='*60}

{history_text}学生问题：{query}

老师回答："""
        
        return prompt
    
    def retrieve_and_build_prompt(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5,
        system_prompt: Optional[str] = None
    ) -> Tuple[str, List[RetrievedDocument]]:
        """
        完整的RAG流程：检索 + 构建提示词
        
        Returns:
            (prompt, retrieved_documents)
        """
        logger.info(f"RAG Pipeline开始处理查询: {query[:100]}...")
        
        # 1. 查询分析
        query_analysis = self.analyze_query(query)
        logger.info(f"查询分析结果: {query_analysis}")
        
        # 2. 多路召回
        documents = self.multi_way_retrieval(query, top_k=top_k*2, query_analysis=query_analysis)
        
        # 3. 重排序
        documents = self.rerank_documents(query, documents, top_n=top_k)
        
        # 4. 上下文压缩
        context = self.compress_context(documents)
        
        # 5. 构建提示词
        prompt = self.build_rag_prompt(query, context, chat_history, system_prompt)
        
        logger.info(f"RAG Pipeline完成，检索到 {len(documents)} 条文档")
        
        return prompt, documents


# 全局RAG Pipeline实例
rag_pipeline = RAGPipeline()
