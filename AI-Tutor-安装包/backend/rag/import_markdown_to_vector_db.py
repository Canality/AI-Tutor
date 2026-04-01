#!/usr/bin/env python3
"""
Markdown 文件到向量数据库导入脚本
用于将 knowledge_base/question 目录下的所有 markdown 题目数据导入向量数据库

使用方法:
    python import_markdown_to_vector_db.py
"""

import os
import sys
import yaml
import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加 backend 到路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from rag.retriever import KnowledgeRetriever
from utils.logger import logger


def parse_markdown_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    解析 markdown 文件，提取元数据和内容
    
    Args:
        file_path: markdown 文件路径
        
    Returns:
        解析后的题目数据字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分离元数据和正文
        parts = content.split('---', 2)
        if len(parts) < 3:
            logger.warning(f"文件格式不正确（缺少 --- 分隔符）: {file_path}")
            return None
        
        metadata_str = parts[1].strip()
        main_content = parts[2].strip()
        
        # 解析元数据
        try:
            metadata = yaml.safe_load(metadata_str)
        except Exception as e:
            logger.warning(f"无法解析元数据: {file_path}, 错误: {e}")
            return None
        
        # 提取题目内容
        question_data = {
            'id': metadata.get('id', ''),
            'source': metadata.get('source', ''),
            'type': metadata.get('type', ''),
            'difficulty': metadata.get('difficulty', 3),
            'knowledge_points': metadata.get('knowledge_points', []),
            'content': extract_question_content(main_content),
            'full_content': main_content,
            'file_path': file_path,
        }
        
        return question_data
        
    except Exception as e:
        logger.error(f"解析文件失败: {file_path}, 错误: {e}")
        return None


def extract_question_content(main_content: str) -> str:
    """
    从 markdown 正文中提取题目内容
    
    Args:
        main_content: markdown 正文内容
        
    Returns:
        提取的题目内容
    """
    lines = main_content.split('\n')
    in_question_section = False
    question_lines = []
    
    for line in lines:
        if '## 一、题目内容' in line:
            in_question_section = True
            continue
        elif line.startswith('## ') and in_question_section:
            break
        
        if in_question_section:
            question_lines.append(line)
    
    return '\n'.join(question_lines).strip()


def format_question_document(question: Dict[str, Any]) -> str:
    """
    将题目格式化为文本文档用于嵌入
    
    包含:
    - 题目内容
    - 知识点标签
    - 来源和类型
    """
    parts = []
    
    # 题目ID和来源
    parts.append(f"【题目ID】{question.get('id', '')}")
    parts.append(f"【来源】{question.get('source', '')}")
    
    # 题目类型和难度
    parts.append(f"【类型】{question.get('type', '')}")
    parts.append(f"【难度】{question.get('difficulty', 3)}/5")
    
    # 题目内容
    content = question.get('content', '')
    if content:
        parts.append(f"【题目】\n{content}")
    
    # 知识点
    knowledge_points = question.get('knowledge_points', [])
    if knowledge_points:
        parts.append(f"【知识点】{', '.join(knowledge_points)}")
    
    return '\n\n'.join(parts)


def format_knowledge_document(question: Dict[str, Any]) -> Optional[str]:
    """
    提取知识点文档
    
    用于知识点检索集合
    """
    knowledge_points = question.get('knowledge_points', [])
    
    if not knowledge_points:
        return None
    
    parts = []
    
    # 知识点说明
    for kp in knowledge_points:
        parts.append(f"知识点：{kp}")
    
    # 添加题目内容作为示例
    content = question.get('content', '')
    if content:
        # 截取前200字符作为示例
        content_preview = content[:200] + '...' if len(content) > 200 else content
        parts.append(f"\n【示例题目】\n{content_preview}")
    
    return '\n'.join(parts)


def find_all_markdown_files(base_dir: str) -> List[str]:
    """
    递归查找所有 markdown 文件
    
    Args:
        base_dir: 基础目录
        
    Returns:
        markdown 文件路径列表
    """
    markdown_files = []
    question_dir = os.path.join(base_dir, 'knowledge_base', 'question')
    
    if not os.path.exists(question_dir):
        logger.error(f"题目目录不存在: {question_dir}")
        return []
    
    for root, dirs, files in os.walk(question_dir):
        for file in files:
            if file.endswith('.md') and not file.startswith('all'):
                markdown_files.append(os.path.join(root, file))
    
    logger.info(f"找到 {len(markdown_files)} 个 markdown 文件")
    return sorted(markdown_files)


def import_to_vector_db():
    """
    将所有 markdown 文件导入向量数据库
    """
    logger.info("=" * 60)
    logger.info("开始导入 Markdown 数据到向量数据库")
    logger.info("=" * 60)
    
    # 查找所有 markdown 文件
    base_dir = os.path.dirname(BACKEND_DIR)
    markdown_files = find_all_markdown_files(base_dir)
    
    if not markdown_files:
        logger.error("没有找到 markdown 文件")
        return False
    
    logger.info(f"准备导入 {len(markdown_files)} 个文件")
    
    # 初始化检索器
    try:
        retriever = KnowledgeRetriever()
        logger.info("向量数据库连接成功")
    except Exception as e:
        logger.error(f"连接向量数据库失败: {e}")
        return False
    
    # 准备数据
    knowledge_docs = []
    knowledge_metas = []
    example_docs = []
    example_metas = []
    
    success_count = 0
    
    for idx, file_path in enumerate(markdown_files):
        logger.info(f"[{idx+1}/{len(markdown_files)}] 处理: {os.path.basename(file_path)}")
        
        question = parse_markdown_file(file_path)
        if not question:
            continue
        
        success_count += 1
        question_id = question.get('id', f'unknown_{idx}')
        
        # 处理知识点文档
        knowledge_doc = format_knowledge_document(question)
        if knowledge_doc:
            knowledge_docs.append(knowledge_doc)
            knowledge_metas.append({
                'question_id': question_id,
                'source': question.get('source', ''),
                'type': 'knowledge',
                'knowledge_points': json.dumps(question.get('knowledge_points', []), ensure_ascii=False),
            })
        
        # 处理例题文档
        example_doc = format_question_document(question)
        if example_doc:
            example_docs.append(example_doc)
            example_metas.append({
                'question_id': question_id,
                'source': question.get('source', ''),
                'type': 'example',
                'difficulty': question.get('difficulty', 3),
                'question_type': question.get('type', ''),
                'knowledge_points': json.dumps(question.get('knowledge_points', []), ensure_ascii=False),
                'file_path': question.get('file_path', ''),
            })
    
    logger.info(f"成功解析 {success_count} 个文件")
    logger.info(f"准备了 {len(knowledge_docs)} 条知识点文档")
    logger.info(f"准备了 {len(example_docs)} 条例题文档")
    
    # 批量插入知识点（分批处理，每批最多32条）
    if knowledge_docs:
        try:
            logger.info("正在插入知识点到向量数据库...")
            batch_size = 32
            for i in range(0, len(knowledge_docs), batch_size):
                batch_docs = knowledge_docs[i:i+batch_size]
                batch_metas = knowledge_metas[i:i+batch_size]
                retriever.batch_insert('knowledge_points', batch_docs, batch_metas)
                logger.info(f"  已插入 {min(i+batch_size, len(knowledge_docs))}/{len(knowledge_docs)} 条知识点")
            logger.info("知识点插入完成")
        except Exception as e:
            logger.error(f"插入知识点失败: {e}")
    
    # 批量插入例题（分批处理，每批最多32条）
    if example_docs:
        try:
            logger.info("正在插入例题到向量数据库...")
            batch_size = 32
            for i in range(0, len(example_docs), batch_size):
                batch_docs = example_docs[i:i+batch_size]
                batch_metas = example_metas[i:i+batch_size]
                retriever.batch_insert('example_questions', batch_docs, batch_metas)
                logger.info(f"  已插入 {min(i+batch_size, len(example_docs))}/{len(example_docs)} 条例题")
            logger.info("例题插入完成")
        except Exception as e:
            logger.error(f"插入例题失败: {e}")
    
    # 验证检索功能
    logger.info("=" * 60)
    logger.info("验证检索功能")
    logger.info("=" * 60)
    
    test_queries = [
        "等差数列求和公式",
        "裂项放缩法证明不等式",
        "递推数列通项公式",
        "数列单调性",
        "周期数列",
    ]
    
    for query in test_queries:
        logger.info(f"\n测试查询: '{query}'")
        try:
            knowledge_results = retriever.search_knowledge(query, top_k=2)
            example_results = retriever.search_examples(query, top_k=2)
            
            logger.info(f"  知识点检索: 找到 {len(knowledge_results)} 条结果")
            for i, r in enumerate(knowledge_results[:1]):
                content_preview = r.get('content', '')[:100]
                logger.info(f"    [{i+1}] {content_preview}...")
            
            logger.info(f"  例题检索: 找到 {len(example_results)} 条结果")
            for i, r in enumerate(example_results[:1]):
                meta = r.get('metadata', {})
                logger.info(f"    [{i+1}] 题目ID: {meta.get('question_id', 'unknown')}")
        except Exception as e:
            logger.error(f"  检索失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Markdown 数据导入完成!")
    logger.info("=" * 60)
    
    return True


def check_database_status():
    """检查向量数据库状态"""
    logger.info("=" * 60)
    logger.info("检查 ChromaDB 向量数据库状态")
    logger.info("=" * 60)
    
    try:
        retriever = KnowledgeRetriever()
        
        # 获取集合信息
        knowledge_count = retriever.knowledge_collection.count()
        example_count = retriever.examples_collection.count()
        
        logger.info(f"知识点集合 (knowledge_points): {knowledge_count} 条记录")
        logger.info(f"例题集合 (example_questions): {example_count} 条例题")
        
        return True
        
    except Exception as e:
        logger.error(f"检查数据库状态失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Markdown 数据到向量数据库导入工具')
    parser.add_argument('--import', action='store_true', dest='do_import', help='导入 Markdown 数据')
    parser.add_argument('--status', action='store_true', help='检查数据库状态')
    
    args = parser.parse_args()
    
    if args.do_import:
        success = import_to_vector_db()
        sys.exit(0 if success else 1)
    
    elif args.status:
        success = check_database_status()
        sys.exit(0 if success else 1)
    
    else:
        # 默认执行导入
        print("Markdown 数据到向量数据库导入工具")
        print("\n用法:")
        print("  python import_markdown_to_vector_db.py --import  # 导入 Markdown 数据")
        print("  python import_markdown_to_vector_db.py --status   # 检查数据库状态")
        print("\n")
        
        # 默认执行导入
        success = import_to_vector_db()
        sys.exit(0 if success else 1)
