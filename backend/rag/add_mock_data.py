import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from rag.retriever import KnowledgeRetriever
from utils.logger import logger




def insert_arithmetic_sequence_data():
    try:
        retriever = KnowledgeRetriever()

        knowledge_docs = [
            "等差数列是指从第二项起，每一项与它的前一项的差等于同一个常数的一种数列，这个常数叫做等差数列的公差，常用字母d表示。",
            "等差数列的通项公式为：an = a1 + (n - 1)d，其中a1是首项，d是公差，n是项数。",
            "等差数列前n项和公式：Sn = n(a1 + an)/2 或 Sn = na1 + n(n-1)d/2。",
        ]
        knowledge_metas = [
            {"type": "定义", "subject": "数学"},
            {"type": "通项公式", "subject": "数学"},
            {"type": "求和公式", "subject": "数学"},
        ]

        example_docs = [
            "例题：已知等差数列首项a1=2，末项a5=10，项数n=5，求前5项和Sn。解：Sn=5×(2+10)/2=30。"
        ]
        example_metas = [{"type": "求和公式例题", "difficulty": "简单"}]

        retriever.batch_insert("knowledge_points", knowledge_docs, knowledge_metas)
        retriever.batch_insert("example_questions", example_docs, example_metas)

        test_knowledge = retriever.search_knowledge("等差数列求和公式", top_k=1)
        test_example = retriever.search_examples("等差数列求和公式例题", top_k=1)

        print("插入成功")

        if test_knowledge:
            print("知识点验证：", test_knowledge[0]["content"][:50] + "...")
        else:
            print("知识点验证：未检索到结果")

        if test_example:
            print("例题验证：", test_example[0]["content"][:50] + "...")
        else:
            print("例题验证：未检索到结果")

    except Exception as e:
        logger.error(f"插入失败: {e}", exc_info=True)
        print(f"插入失败: {e}")



if __name__ == "__main__":
    insert_arithmetic_sequence_data()
