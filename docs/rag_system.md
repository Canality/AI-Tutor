# RAG系统文档

> AI Tutor 检索增强生成 (RAG) 系统文档
> 最后更新：2026-03-27

---

## 📋 概述

RAG (Retrieval-Augmented Generation) 系统为AI Tutor提供知识检索和答案生成增强功能。通过将向量检索与LLM生成结合，使AI辅导更加准确、有依据。

## 🏗️ 系统架构

```
用户提问
    ↓
[查询分析] → 提取关键概念、识别查询类型
    ↓
[多路召回] → 向量检索(知识点+例题) + 关键词匹配
    ↓
[重排序] → 综合分数排序
    ↓
[上下文压缩] → 控制token数量
    ↓
[提示词组装] → 构建RAG增强提示词
    ↓
[LLM生成] → 生成最终回答
```

---

## 📁 文件结构

```
backend/rag/
├── __init__.py           # 模块初始化
├── retriever.py          # 基础检索器 (KnowledgeRetriever)
├── pipeline.py           # RAG Pipeline (完整流程)
├── init_chroma_db.py     # 向量数据库初始化
├── add_mock_data.py      # 测试数据插入
└── test_rag.py           # RAG测试脚本
```

---

## 🔧 核心组件

### 1. KnowledgeRetriever (retriever.py)

基础向量检索器，封装ChromaDB操作。

```python
from rag.retriever import KnowledgeRetriever

retriever = KnowledgeRetriever()

# 检索知识点
knowledge_results = retriever.search_knowledge("等差数列求和", top_k=3)

# 检索例题
example_results = retriever.search_examples("裂项放缩", top_k=3)

# 批量插入
retriever.batch_insert("knowledge_points", documents, metadatas)
```

### 2. RAGPipeline (pipeline.py)

完整的RAG流程封装。

```python
from rag.pipeline import rag_pipeline

# 完整RAG流程
prompt, documents = rag_pipeline.retrieve_and_build_prompt(
    query="递推数列怎么求通项？",
    chat_history=None,
    top_k=5
)

# 分步使用
analysis = rag_pipeline.analyze_query(query)
documents = rag_pipeline.multi_way_retrieval(query, top_k=5)
documents = rag_pipeline.rerank_documents(query, documents, top_n=3)
context = rag_pipeline.compress_context(documents)
prompt = rag_pipeline.build_rag_prompt(query, context)
```

---

## 🚀 API接口

### RAG API端点

Base URL: `/api/rag`

#### 1. 检索文档

```http
POST /api/rag/search
```

请求体：
```json
{
    "query": "等差数列求和公式",
    "top_k": 5,
    "search_type": "mixed"
}
```

响应：
```json
{
    "success": true,
    "query": "等差数列求和公式",
    "results": [
        {
            "content": "知识点内容...",
            "metadata": {"question_id": "E_123", ...},
            "score": 0.85,
            "doc_type": "knowledge"
        }
    ],
    "total": 5
}
```

#### 2. 生成RAG提示词

```http
POST /api/rag/generate-prompt
```

请求体：
```json
{
    "query": "递推数列怎么求通项？",
    "chat_history": [
        {"role": "user", "content": "什么是等差数列？"},
        {"role": "assistant", "content": "等差数列是指..."}
    ],
    "top_k": 5
}
```

响应：
```json
{
    "success": true,
    "query": "递推数列怎么求通项？",
    "prompt": "完整的RAG增强提示词...",
    "retrieved_documents": [...],
    "total_docs": 5
}
```

#### 3. 获取统计信息

```http
GET /api/rag/stats
```

响应：
```json
{
    "success": true,
    "collections": [
        {"name": "knowledge_points", "count": 33},
        {"name": "example_questions", "count": 33}
    ]
}
```

---

## 🧪 测试

### 运行测试脚本

```bash
cd backend

# 运行所有测试
python rag/test_rag.py --test all

# 仅测试检索功能
python rag/test_rag.py --test retriever

# 仅测试Pipeline
python rag/test_rag.py --test pipeline

# 交互式测试
python rag/test_rag.py --test interactive
```

### API测试示例

```bash
# 测试检索API
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "等差数列求和", "top_k": 3}'

# 测试RAG提示词生成
curl -X POST http://localhost:8000/api/rag/generate-prompt \
  -H "Content-Type: application/json" \
  -d '{"query": "递推数列通项公式", "top_k": 5}'
```

---

## 📊 数据集合

### knowledge_points (知识点集合)

存储数列相关的知识点、公式、定理等。

元数据字段：
- `question_id`: 题目ID
- `source`: 来源
- `type`: 类型
- `knowledge_points`: 知识点列表(JSON)
- `method_tags`: 方法标签(JSON)

### example_questions (例题集合)

存储具体的例题和解答。

元数据字段：
- `question_id`: 题目ID
- `source`: 来源
- `type`: 类型(example)
- `difficulty`: 难度(1-5)
- `question_type`: 题型
- `knowledge_points`: 知识点列表(JSON)
- `page`: 页码

---

## 🔍 查询分析

系统自动分析查询类型：

| 查询类型 | 说明 | 示例 |
|---------|------|------|
| knowledge | 知识点查询 | "什么是等差数列？" |
| example | 例题查询 | "给我一道递推数列例题" |
| mixed | 混合查询 | "递推数列怎么求通项？" |

提取的关键概念：
- 等差数列、等比数列
- 递推数列、通项公式
- 裂项放缩、数学归纳法
- 数列求和、不等式证明

---

## ⚙️ 配置参数

### 环境变量 (.env)

```bash
# 向量模型配置
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# ChromaDB存储路径
CHROMA_PERSIST_DIR=./storage/chroma
```

### RAG Pipeline参数

```python
# 检索数量
top_k = 5  # 最终返回的文档数

# 上下文压缩
max_tokens = 1500  # 最大token数

# 重排序
top_n = 5  # 重排序后保留的文档数
```

---

## 🔄 工作流程

### 1. 查询分析
```python
analysis = rag_pipeline.analyze_query(query)
# {
#     'query_type': 'knowledge',
#     'key_concepts': ['等差数列', '通项公式'],
#     'difficulty_hint': None,
#     'clean_query': '什么是等差数列的通项公式？'
# }
```

### 2. 多路召回
- 向量检索知识点集合
- 向量检索例题集合
- 关键词匹配补充

### 3. 重排序
综合以下因素计算最终分数：
- 向量相似度分数
- 关键词匹配度
- 文档类型权重

### 4. 上下文压缩
- 优先保留高分文档
- 截断过长文档
- 添加文档分隔标记

### 5. 提示词组装
```
[系统提示词]
+
[相关参考资料]
+
[历史对话]
+
[当前问题]
```

---

## 🛠️ 扩展开发

### 添加新的检索集合

```python
# 在 retriever.py 中
self.new_collection = self.client.get_or_create_collection(
    name="new_collection",
)

# 添加检索方法
def search_new_collection(self, query: str, top_k: int = 3):
    query_vector = self.embedding_function([query])[0]
    results = self.new_collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )
    return self._format_query_results(results)
```

### 自定义重排序策略

```python
def custom_rerank(self, query: str, documents: List[RetrievedDocument]) -> List[RetrievedDocument]:
    # 实现自定义排序逻辑
    for doc in documents:
        # 自定义评分
        doc.score = calculate_custom_score(query, doc)
    
    documents.sort(key=lambda x: x.score, reverse=True)
    return documents
```

---

## 📈 性能优化

1. **批量插入**：使用batch_insert分批插入，每批最多32条
2. **Token控制**：上下文压缩限制最大token数
3. **缓存策略**：可考虑添加查询结果缓存
4. **异步检索**：使用异步接口提高并发性能

---

## 🐛 常见问题

### Q: 检索结果为空？
- 检查向量数据库是否已初始化
- 检查查询文本是否为空
- 检查集合中是否有数据

### Q: 维度不匹配错误？
- 删除旧的ChromaDB存储目录
- 重新运行初始化脚本

### Q: Embedding API调用失败？
- 检查OPENAI_API_KEY配置
- 检查网络连接
- 查看API配额

---

## 📝 更新日志

### 2026-03-27
- 初始版本发布
- 实现完整的RAG Pipeline
- 添加多路召回和重排序
- 添加上下文压缩
- 添加API接口
