#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 向量数据库初始化脚本 - 改进版

数据切分策略：
1. 知识点文档 - 提取题目的知识点和方法标签
2. 例题文档 - 题目内容 + 简要解答思路（用于检索相似例题）
3. 解题模式文档 - 解答步骤的拆解（用于引导学生解题）

使用方法:
    python init_chroma_db_v2.py --init
"""

import os
import sys
import json
import uuid
from typing import List, Dict, Any, Optional

# 添加backend到路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from rag.retriever import KnowledgeRetriever
from utils.config import settings
from utils.logger import logger


def load_questions(dataset_path: str) -> List[Dict[str, Any]]:
    """加载题目数据集"""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        questions = data.get('questions', [])
        logger.info(f"成功加载 {len(questions)} 道题目")
        return questions
    except Exception as e:
        logger.error(f"加载题目数据失败: {e}")
        return []


def truncate_text(text: str, max_tokens: int = 400) -> str:
    """截断文本以控制token数量"""
    if not text:
        return text
    max_chars = int(max_tokens * 2)  # 简单估算
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[内容已截断]"
    return text


# ============ 数据切分策略 ============

def create_knowledge_document(question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    创建知识点文档
    
    用于：理解题目涉及的知识点
    """
    knowledge_points = question.get('knowledge_points', [])
    method_tags = question.get('method_tags', [])
    error_prone_points = question.get('error_prone_points', [])
    
    if not knowledge_points and not method_tags:
        return None
    
    # 构建知识点文档
    parts = []
    parts.append(f"【题目ID】{question.get('id', '')}")
    parts.append(f"【来源】{question.get('source', '')}")
    
    # 知识点
    if knowledge_points:
        parts.append(f"\n【涉及知识点】")
        for kp in knowledge_points:
            parts.append(f"- {kp}")
    
    # 解题方法
    if method_tags:
        parts.append(f"\n【解题方法】")
        for mt in method_tags:
            parts.append(f"- {mt}")
    
    # 易错点
    if error_prone_points:
        parts.append(f"\n【易错点】")
        for ep in error_prone_points:
            parts.append(f"- {ep}")
    
    # 添加题目内容预览
    content = question.get('content', '')
    if content:
        parts.append(f"\n【题目预览】\n{truncate_text(content, 200)}")
    
    return {
        'content': '\n'.join(parts),
        'metadata': {
            'question_id': question.get('id', ''),
            'source': question.get('source', ''),
            'doc_type': 'knowledge',
            'knowledge_points': json.dumps(knowledge_points, ensure_ascii=False),
            'method_tags': json.dumps(method_tags, ensure_ascii=False),
            'difficulty': question.get('difficulty', 3),
        }
    }


def create_example_document(question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    创建例题文档
    
    用于：
    1. 推荐相似例题时检索
    2. 快速了解题目内容和难度
    """
    content = question.get('content', '')
    if not content:
        return None
    
    parts = []
    parts.append(f"【题目ID】{question.get('id', '')}")
    parts.append(f"【来源】{question.get('source', '')}")
    parts.append(f"【类型】{question.get('type', '')}")
    parts.append(f"【难度】{question.get('difficulty', 3)}/5")
    
    # 知识点标签
    knowledge_points = question.get('knowledge_points', [])
    if knowledge_points:
        parts.append(f"【知识点】{', '.join(knowledge_points)}")
    
    # 方法标签
    method_tags = question.get('method_tags', [])
    if method_tags:
        parts.append(f"【方法】{', '.join(method_tags)}")
    
    # 题目内容
    parts.append(f"\n【题目内容】\n{truncate_text(content, 300)}")
    
    # 简要解答思路（只取每个part的标题，不取详细步骤）
    parts_data = question.get('parts', [])
    if parts_data:
        parts.append("\n【解答结构】")
        for p in parts_data:
            part_id = p.get('part_id', '')
            title = p.get('title', '')
            if title:
                parts.append(f"({part_id}) {title}")
    
    return {
        'content': '\n'.join(parts),
        'metadata': {
            'question_id': question.get('id', ''),
            'source': question.get('source', ''),
            'doc_type': 'example',
            'difficulty': question.get('difficulty', 3),
            'question_type': question.get('type', ''),
            'knowledge_points': json.dumps(knowledge_points, ensure_ascii=False),
            'method_tags': json.dumps(method_tags, ensure_ascii=False),
            'page': question.get('page', 0),
        }
    }


def create_solution_pattern_documents(question: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    创建解题模式文档
    
    将每个解答步骤拆分为独立文档
    
    用于：引导学生解题时，检索相似题目的解题步骤和引导方式
    """
    documents = []
    parts_data = question.get('parts', [])
    
    if not parts_data:
        # 如果没有分步解答，创建一个整体文档
        content = question.get('content', '')
        if content:
            documents.append({
                'content': f"【题目ID】{question.get('id', '')}\n\n【题目】\n{truncate_text(content, 400)}",
                'metadata': {
                    'question_id': question.get('id', ''),
                    'source': question.get('source', ''),
                    'doc_type': 'solution_pattern',
                    'part_id': 'full',
                    'difficulty': question.get('difficulty', 3),
                    'knowledge_points': json.dumps(question.get('knowledge_points', []), ensure_ascii=False),
                }
            })
        return documents
    
    # 为每个解答步骤创建文档
    for part in parts_data:
        part_id = part.get('part_id', '')
        title = part.get('title', '')
        solution = part.get('solution', '')
        
        if not solution:
            continue
        
        parts = []
        parts.append(f"【题目ID】{question.get('id', '')}")
        parts.append(f"【解答步骤】({part_id}) {title}")
        parts.append(f"【难度】{question.get('difficulty', 3)}/5")
        
        # 知识点
        knowledge_points = question.get('knowledge_points', [])
        if knowledge_points:
            parts.append(f"【相关知识点】{', '.join(knowledge_points)}")
        
        # 方法
        method_tags = question.get('method_tags', [])
        if method_tags:
            parts.append(f"【解题方法】{', '.join(method_tags)}")
        
        # 详细解答步骤
        parts.append(f"\n【详细引导】\n{truncate_text(solution, 400)}")
        
        documents.append({
            'content': '\n'.join(parts),
            'metadata': {
                'question_id': question.get('id', ''),
                'source': question.get('source', ''),
                'doc_type': 'solution_pattern',
                'part_id': part_id,
                'part_title': title,
                'difficulty': question.get('difficulty', 3),
                'knowledge_points': json.dumps(knowledge_points, ensure_ascii=False),
                'method_tags': json.dumps(method_tags, ensure_ascii=False),
            }
        })
    
    return documents


# ============ 初始化流程 ============

def init_chroma_database():
    """初始化ChromaDB向量数据库"""
    logger.info("=" * 60)
    logger.info("开始初始化 ChromaDB 向量数据库 (改进版)")
    logger.info("=" * 60)
    
    # 检查数据集文件
    dataset_path = os.path.join(BACKEND_DIR, 'dataset', 'member_E_questions.json')
    if not os.path.exists(dataset_path):
        logger.error(f"数据集文件不存在: {dataset_path}")
        return False
    
    # 加载题目数据
    questions = load_questions(dataset_path)
    if not questions:
        logger.error("没有加载到题目数据")
        return False
    
    logger.info(f"准备处理 {len(questions)} 道题目")
    
    # 初始化检索器
    try:
        retriever = KnowledgeRetriever()
        logger.info("向量数据库连接成功")
    except Exception as e:
        logger.error(f"连接向量数据库失败: {e}")
        return False
    
    # 准备三种类型的文档
    knowledge_docs = []
    example_docs = []
    solution_pattern_docs = []
    
    for question in questions:
        # 1. 知识点文档
        knowledge_doc = create_knowledge_document(question)
        if knowledge_doc:
            knowledge_docs.append(knowledge_doc)
        
        # 2. 例题文档
        example_doc = create_example_document(question)
        if example_doc:
            example_docs.append(example_doc)
        
        # 3. 解题模式文档（多个步骤）
        solution_docs = create_solution_pattern_documents(question)
        solution_pattern_docs.extend(solution_docs)
    
    logger.info(f"准备了 {len(knowledge_docs)} 条知识点文档")
    logger.info(f"准备了 {len(example_docs)} 条例题文档")
    logger.info(f"准备了 {len(solution_pattern_docs)} 条解题模式文档")
    
    # 批量插入（分批处理，每批最多32条）
    batch_size = 32
    
    # 插入知识点
    if knowledge_docs:
        try:
            logger.info("正在插入知识点到向量数据库...")
            for i in range(0, len(knowledge_docs), batch_size):
                batch = knowledge_docs[i:i+batch_size]
                retriever.batch_insert(
                    'knowledge_points',
                    [d['content'] for d in batch],
                    [d['metadata'] for d in batch]
                )
                logger.info(f"  已插入 {min(i+batch_size, len(knowledge_docs))}/{len(knowledge_docs)} 条知识点")
        except Exception as e:
            logger.error(f"插入知识点失败: {e}")
    
    # 插入例题
    if example_docs:
        try:
            logger.info("正在插入例题到向量数据库...")
            for i in range(0, len(example_docs), batch_size):
                batch = example_docs[i:i+batch_size]
                retriever.batch_insert(
                    'example_questions',
                    [d['content'] for d in batch],
                    [d['metadata'] for d in batch]
                )
                logger.info(f"  已插入 {min(i+batch_size, len(example_docs))}/{len(example_docs)} 条例题")
        except Exception as e:
            logger.error(f"插入例题失败: {e}")
    
    # 插入解题模式（使用同一个集合，通过metadata区分）
    if solution_pattern_docs:
        try:
            logger.info("正在插入解题模式到向量数据库...")
            for i in range(0, len(solution_pattern_docs), batch_size):
                batch = solution_pattern_docs[i:i+batch_size]
                retriever.batch_insert(
                    'example_questions',  # 使用example_questions集合
                    [d['content'] for d in batch],
                    [d['metadata'] for d in batch]
                )
                logger.info(f"  已插入 {min(i+batch_size, len(solution_pattern_docs))}/{len(solution_pattern_docs)} 条解题模式")
        except Exception as e:
            logger.error(f"插入解题模式失败: {e}")
    
    # 验证检索功能
    logger.info("=" * 60)
    logger.info("验证检索功能")
    logger.info("=" * 60)
    
    test_queries = [
        ("等差数列求和公式", "knowledge"),
        ("裂项放缩法证明不等式", "example"),
        ("递推数列通项公式", "example"),
        ("数学归纳法证明步骤", "solution_pattern"),
    ]
    
    for query, expected_type in test_queries:
        logger.info(f"\n测试查询: '{query}' (期望类型: {expected_type})")
        try:
            # 检索知识点
            knowledge_results = retriever.search_knowledge(query, top_k=2)
            logger.info(f"  知识点检索: 找到 {len(knowledge_results)} 条结果")
            
            # 检索例题/解题模式
            example_results = retriever.search_examples(query, top_k=2)
            logger.info(f"  例题/解题模式检索: 找到 {len(example_results)} 条结果")
            
            for i, r in enumerate(example_results[:1]):
                meta = r.get('metadata', {})
                doc_type = meta.get('doc_type', 'unknown')
                qid = meta.get('question_id', 'unknown')
                logger.info(f"    [{i+1}] 类型:{doc_type} | ID:{qid}")
                
        except Exception as e:
            logger.error(f"  检索失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("ChromaDB 向量数据库初始化完成!")
    logger.info("=" * 60)
    
    return True


def check_database_status():
    """检查向量数据库状态"""
    logger.info("=" * 60)
    logger.info("检查 ChromaDB 向量数据库状态")
    logger.info("=" * 60)
    
    try:
        retriever = KnowledgeRetriever()
        
        knowledge_count = retriever.knowledge_collection.count()
        example_count = retriever.examples_collection.count()
        
        logger.info(f"知识点集合 (knowledge_points): {knowledge_count} 条记录")
        logger.info(f"例题集合 (example_questions): {example_count} 条记录")
        
        # 统计解题模式文档数量
        try:
            solution_patterns = retriever.examples_collection.get(
                where={"doc_type": "solution_pattern"}
            )
            if solution_patterns and solution_patterns.get('ids'):
                logger.info(f"其中解题模式文档: {len(solution_patterns['ids'])} 条")
        except Exception as e:
            logger.warning(f"统计解题模式失败: {e}")
        
        logger.info(f"\n数据库存储路径: {settings.chroma_persist_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"检查数据库状态失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChromaDB 向量数据库管理工具 (改进版)')
    parser.add_argument('--init', action='store_true', help='初始化并导入数据')
    parser.add_argument('--status', action='store_true', help='检查数据库状态')
    
    args = parser.parse_args()
    
    if args.init:
        success = init_chroma_database()
        sys.exit(0 if success else 1)
    elif args.status:
        success = check_database_status()
        sys.exit(0 if success else 1)
    else:
        print("ChromaDB 向量数据库管理工具 (改进版)")
        print("\n数据切分策略:")
        print("  1. 知识点文档 - 提取题目的知识点、方法、易错点")
        print("  2. 例题文档 - 题目内容+简要解答结构（用于推荐相似例题）")
        print("  3. 解题模式文档 - 详细解答步骤（用于引导学生解题）")
        print("\n用法:")
        print("  python init_chroma_db_v2.py --init    # 初始化数据库")
        print("  python init_chroma_db_v2.py --status  # 检查数据库状态")
        print("\n")
        check_database_status()
