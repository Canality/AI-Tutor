#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统测试脚本

测试内容：
1. 向量检索功能
2. RAG Pipeline完整流程
3. API接口测试

使用方法：
    python test_rag.py
"""

import os
import sys
import json
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加backend到路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from rag.pipeline import rag_pipeline, RetrievedDocument
from rag.retriever import KnowledgeRetriever
from utils.logger import logger


def test_retriever():
    """测试基础检索功能"""
    print("\n" + "="*60)
    print("测试1: 基础检索功能")
    print("="*60)
    
    retriever = KnowledgeRetriever()
    
    test_queries = [
        "等差数列求和公式",
        "裂项放缩法证明不等式",
        "递推数列通项公式",
        "数学归纳法证明",
    ]
    
    for query in test_queries:
        print(f"\n🔍 查询: '{query}'")
        print("-" * 40)
        
        # 检索知识点
        knowledge_results = retriever.search_knowledge(query, top_k=2)
        print(f"  📚 知识点: {len(knowledge_results)} 条")
        for i, r in enumerate(knowledge_results, 1):
            content = r.get('content', '')[:80]
            distance = r.get('distance', 0)
            print(f"     [{i}] [距离:{distance:.4f}] {content}...")
        
        # 检索例题
        example_results = retriever.search_examples(query, top_k=2)
        print(f"  📝 例题: {len(example_results)} 条")
        for i, r in enumerate(example_results, 1):
            meta = r.get('metadata', {})
            qid = meta.get('question_id', 'unknown')
            distance = r.get('distance', 0)
            print(f"     [{i}] [距离:{distance:.4f}] ID:{qid}")


def test_rag_pipeline():
    """测试RAG Pipeline完整流程"""
    print("\n" + "="*60)
    print("测试2: RAG Pipeline完整流程")
    print("="*60)
    
    test_questions = [
        "什么是等差数列的通项公式？",
        "请给我一道裂项放缩法的例题",
        "递推数列怎么求通项？",
    ]
    
    for question in test_questions:
        print(f"\n❓ 问题: '{question}'")
        print("-" * 40)
        
        # 运行RAG Pipeline
        prompt, documents = rag_pipeline.retrieve_and_build_prompt(
            query=question,
            top_k=3
        )
        
        print(f"  ✅ 检索到 {len(documents)} 条文档")
        
        # 显示检索结果
        for i, doc in enumerate(documents, 1):
            print(f"     [{i}] [{doc.doc_type}] 分数:{doc.score:.3f}")
            # 显示元数据
            meta = doc.metadata
            if meta.get('question_id'):
                print(f"         ID: {meta.get('question_id')}")
            if meta.get('knowledge_points'):
                print(f"         知识点: {meta.get('knowledge_points')}")
        
        # 显示生成的提示词长度
        print(f"  📝 生成提示词长度: {len(prompt)} 字符")


def test_query_analysis():
    """测试查询分析功能"""
    print("\n" + "="*60)
    print("测试3: 查询分析功能")
    print("="*60)
    
    test_queries = [
        "什么是等差数列的定义？",
        "给我一道难度3的递推数列例题",
        "怎么用裂项放缩法证明不等式？",
        "等比数列求和公式是什么",
    ]
    
    for query in test_queries:
        print(f"\n🔍 查询: '{query}'")
        analysis = rag_pipeline.analyze_query(query)
        print(f"  类型: {analysis['query_type']}")
        print(f"  关键概念: {analysis['key_concepts']}")
        if analysis['difficulty_hint']:
            print(f"  难度提示: {analysis['difficulty_hint']}")


def test_reranking():
    """测试重排序功能"""
    print("\n" + "="*60)
    print("测试4: 重排序功能")
    print("="*60)
    
    query = "裂项放缩法证明不等式"
    print(f"\n🔍 查询: '{query}'")
    
    # 多路召回
    documents = rag_pipeline.multi_way_retrieval(query, top_k=5)
    print(f"\n📥 召回阶段: {len(documents)} 条文档")
    for i, doc in enumerate(documents[:5], 1):
        print(f"     [{i}] [{doc.doc_type}] 初始分数:{doc.score:.3f}")
    
    # 重排序
    reranked = rag_pipeline.rerank_documents(query, documents, top_n=5)
    print(f"\n🔄 重排序后:")
    for i, doc in enumerate(reranked, 1):
        print(f"     [{i}] [{doc.doc_type}] 最终分数:{doc.score:.3f}")


def test_context_compression():
    """测试上下文压缩"""
    print("\n" + "="*60)
    print("测试5: 上下文压缩")
    print("="*60)
    
    query = "递推数列"
    documents = rag_pipeline.multi_way_retrieval(query, top_k=5)
    
    print(f"\n📄 原始文档总字符数: {sum(len(d.content) for d in documents)}")
    
    # 测试不同压缩限制
    for max_tokens in [500, 1000, 1500]:
        context = rag_pipeline.compress_context(documents, max_tokens=max_tokens)
        print(f"  限制 {max_tokens} tokens -> 实际 {len(context)} 字符")


def interactive_test():
    """交互式测试"""
    print("\n" + "="*60)
    print("交互式RAG测试")
    print("="*60)
    print("输入问题进行RAG检索（输入 'quit' 退出）\n")
    
    while True:
        query = input("❓ 请输入问题: ").strip()
        if query.lower() in ('quit', 'exit', 'q'):
            break
        
        if not query:
            continue
        
        print("\n" + "-"*60)
        
        # 查询分析
        analysis = rag_pipeline.analyze_query(query)
        print(f"📊 查询分析:")
        print(f"   类型: {analysis['query_type']}")
        print(f"   关键概念: {analysis['key_concepts']}")
        
        # RAG检索
        prompt, documents = rag_pipeline.retrieve_and_build_prompt(query, top_k=3)
        
        print(f"\n📚 检索结果 ({len(documents)} 条):")
        for i, doc in enumerate(documents, 1):
            print(f"   [{i}] [{doc.doc_type}] 分数:{doc.score:.3f}")
            content_preview = doc.content[:100].replace('\n', ' ')
            print(f"       {content_preview}...")
        
        print(f"\n📝 生成的提示词预览 (前500字符):")
        print(prompt[:500])
        print("..." if len(prompt) > 500 else "")
        print("-"*60 + "\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG系统测试工具')
    parser.add_argument('--test', choices=['all', 'retriever', 'pipeline', 'analysis', 'rerank', 'compress', 'interactive'],
                       default='all', help='选择测试项目')
    
    args = parser.parse_args()
    
    print("="*60)
    print("AI Tutor RAG系统测试")
    print("="*60)
    
    try:
        if args.test == 'all':
            test_retriever()
            test_rag_pipeline()
            test_query_analysis()
            test_reranking()
            test_context_compression()
        elif args.test == 'retriever':
            test_retriever()
        elif args.test == 'pipeline':
            test_rag_pipeline()
        elif args.test == 'analysis':
            test_query_analysis()
        elif args.test == 'rerank':
            test_reranking()
        elif args.test == 'compress':
            test_context_compression()
        elif args.test == 'interactive':
            interactive_test()
        
        print("\n" + "="*60)
        print("✅ 测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
