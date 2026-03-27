#!/usr/bin/env python3
"""
ChromaDB 向量数据库初始化脚本
用于将题目数据导入向量数据库，支持RAG检索

使用方法:
    python init_chroma_db.py

功能:
    1. 读取 member_E_questions.json 题目数据
    2. 生成文本嵌入（使用硅基流动Embedding API）
    3. 存入ChromaDB向量数据库
    4. 支持按知识点、题型、难度等元数据检索
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

from rag.retriever import KnowledgeRetriever, SiliconFlowEmbeddingFunction
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


def format_question_document(question: Dict[str, Any]) -> str:
    """
    将题目格式化为文本文档用于嵌入
    
    包含:
    - 题目内容
    - 知识点标签
    - 方法标签
    - 易错点
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
    
    # 方法标签
    method_tags = question.get('method_tags', [])
    if method_tags:
        parts.append(f"【解题方法】{', '.join(method_tags)}")
    
    # 易错点
    error_prone_points = question.get('error_prone_points', [])
    if error_prone_points:
        parts.append(f"【易错点】{', '.join(error_prone_points)}")
    
    # 特色标签
    feature_tags = question.get('feature_tags', [])
    if feature_tags:
        parts.append(f"【题目特点】{', '.join(feature_tags)}")
    
    return '\n\n'.join(parts)


def format_knowledge_document(question: Dict[str, Any]) -> Optional[str]:
    """
    提取知识点文档
    
    用于知识点检索集合
    """
    knowledge_points = question.get('knowledge_points', [])
    method_tags = question.get('method_tags', [])
    
    if not knowledge_points and not method_tags:
        return None
    
    parts = []
    
    # 知识点说明
    for kp in knowledge_points:
        parts.append(f"知识点：{kp}")
    
    # 相关方法
    for mt in method_tags:
        parts.append(f"解题方法：{mt}")
    
    # 添加题目内容作为示例
    content = question.get('content', '')
    if content:
        # 截取前200字符作为示例
        content_preview = content[:200] + '...' if len(content) > 200 else content
        parts.append(f"\n【示例题目】\n{content_preview}")
    
    return '\n'.join(parts)


def truncate_text(text: str, max_tokens: int = 400) -> str:
    """
    截断文本以控制token数量
    假设平均每个汉字/字符约1-1.5个token
    """
    if not text:
        return text
    # 简单估算：每个字符约1.5个token
    max_chars = int(max_tokens / 1.5)
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def format_example_document(question: Dict[str, Any]) -> Optional[str]:
    """
    提取例题文档
    
    用于例题检索集合
    """
    content = question.get('content', '')
    if not content:
        return None
    
    parts = []
    
    # 题目信息
    parts.append(f"【题目ID】{question.get('id', '')}")
    parts.append(f"【来源】{question.get('source', '')}")
    parts.append(f"【类型】{question.get('type', '')}")
    parts.append(f"【难度】{question.get('difficulty', 3)}/5")
    
    # 完整题目内容（截断以控制token数）
    parts.append(f"\n【题目内容】\n{truncate_text(content, 300)}")
    
    # 如果有分步解答，也加入（简短版本）
    parts_data = question.get('parts', [])
    if parts_data:
        parts.append("\n【分步解答】")
        for p in parts_data:
            part_id = p.get('part_id', '')
            title = p.get('title', '')
            solution = p.get('solution', '')
            if title:
                parts.append(f"\n({part_id}) {title}")
            if solution:
                parts.append(truncate_text(solution, 100))
    
    return '\n'.join(parts)


def init_chroma_database():
    """
    初始化ChromaDB向量数据库
    
    创建两个集合:
    1. knowledge_points - 知识点集合
    2. example_questions - 例题集合
    """
    logger.info("=" * 60)
    logger.info("开始初始化 ChromaDB 向量数据库")
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
    
    logger.info(f"准备导入 {len(questions)} 道题目到向量数据库")
    
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
    
    for idx, question in enumerate(questions):
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
                'method_tags': json.dumps(question.get('method_tags', []), ensure_ascii=False),
            })
        
        # 处理例题文档
        example_doc = format_example_document(question)
        if example_doc:
            example_docs.append(example_doc)
            example_metas.append({
                'question_id': question_id,
                'source': question.get('source', ''),
                'type': 'example',
                'difficulty': question.get('difficulty', 3),
                'question_type': question.get('type', ''),
                'knowledge_points': json.dumps(question.get('knowledge_points', []), ensure_ascii=False),
                'page': question.get('page', 0),
            })
    
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
        "数学归纳法证明",
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
        
        # 获取集合信息
        knowledge_count = retriever.knowledge_collection.count()
        example_count = retriever.examples_collection.count()
        
        logger.info(f"知识点集合 (knowledge_points): {knowledge_count} 条记录")
        logger.info(f"例题集合 (example_questions): {example_count} 条例题")
        
        # 检查存储路径
        logger.info(f"\n数据库存储路径: {settings.chroma_persist_dir}")
        
        if os.path.exists(settings.chroma_persist_dir):
            files = os.listdir(settings.chroma_persist_dir)
            logger.info(f"存储目录内容: {files}")
        else:
            logger.warning("存储目录不存在!")
        
        return True
        
    except Exception as e:
        logger.error(f"检查数据库状态失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChromaDB 向量数据库管理工具')
    parser.add_argument('--init', action='store_true', help='初始化并导入数据')
    parser.add_argument('--status', action='store_true', help='检查数据库状态')
    parser.add_argument('--test', action='store_true', help='测试检索功能')
    
    args = parser.parse_args()
    
    if args.init:
        success = init_chroma_database()
        sys.exit(0 if success else 1)
    
    elif args.status:
        success = check_database_status()
        sys.exit(0 if success else 1)
    
    elif args.test:
        # 运行测试查询
        logger.info("=" * 60)
        logger.info("测试向量检索功能")
        logger.info("=" * 60)
        
        try:
            retriever = KnowledgeRetriever()
            
            while True:
                query = input("\n请输入查询内容 (或输入 'quit' 退出): ").strip()
                if query.lower() in ('quit', 'exit', 'q'):
                    break
                
                if not query:
                    continue
                
                print(f"\n🔍 查询: '{query}'")
                print("-" * 60)
                
                # 知识点检索
                print("\n📚 相关知识点:")
                knowledge_results = retriever.search_knowledge(query, top_k=3)
                if knowledge_results:
                    for i, r in enumerate(knowledge_results, 1):
                        content = r.get('content', '')[:200]
                        distance = r.get('distance', 0)
                        print(f"  {i}. [{distance:.4f}] {content}...")
                else:
                    print("  未找到相关知识点")
                
                # 例题检索
                print("\n📝 相关例题:")
                example_results = retriever.search_examples(query, top_k=3)
                if example_results:
                    for i, r in enumerate(example_results, 1):
                        meta = r.get('metadata', {})
                        qid = meta.get('question_id', 'unknown')
                        difficulty = meta.get('difficulty', '?')
                        distance = r.get('distance', 0)
                        content = r.get('content', '')[:150]
                        print(f"  {i}. [{distance:.4f}] 难度{difficulty}/5 | ID:{qid}")
                        print(f"     {content}...")
                else:
                    print("  未找到相关例题")
                
                print("-" * 60)
        
        except KeyboardInterrupt:
            print("\n\n已退出")
        except Exception as e:
            logger.error(f"测试失败: {e}")
    
    else:
        # 默认执行初始化和状态检查
        print("ChromaDB 向量数据库管理工具")
        print("\n用法:")
        print("  python init_chroma_db.py --init    # 初始化数据库并导入数据")
        print("  python init_chroma_db.py --status  # 检查数据库状态")
        print("  python init_chroma_db.py --test    # 交互式测试检索")
        print("\n")
        
        # 默认执行状态检查
        check_database_status()
