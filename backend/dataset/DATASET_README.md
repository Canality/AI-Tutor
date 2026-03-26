# AI Tutor 题目数据结构化规范

## 📁 文件存储方案建议

### 推荐方案：**单个 JSON 文件（所有题目合并）**

**文件路径**: `backend/dataset/sequence_problems.json`

**结构**:
```json
{
  "metadata": {
    "version": "1.0",
    "total_count": 150,
    "last_updated": "2026-03-26",
    "subject": "高中数学数列",
    "contributors": ["member_A", "member_B", "member_C", "member_D", "member_E"]
  },
  "questions": [
    { /* 题目1 */ },
    { /* 题目2 */ },
    ...
  ]
}
```

### 为什么不推荐一个题目一个 JSON 文件？

| 对比项 | 单文件（推荐） | 多文件（不推荐） |
|--------|---------------|-----------------|
| **加载速度** | 一次读取，快 | 需要遍历目录，慢 |
| **RAG 索引构建** | 直接解析，简单 | 需要批量读取，复杂 |
| **版本控制** | 一个文件易管理 | 文件太多难追踪 |
| **部署传输** | 单个文件方便 | 大量小文件效率低 |
| **数据一致性** | 统一格式易校验 | 分散难保证一致 |

---

## 📋 题目数据结构模板

### 完整字段说明

```json
{
  "id": "string",                    // 唯一标识，格式：成员代号_序号，如 "C_072"
  "source": "string",                // 来源：书名+页码+题号
  "type": "string",                  // 题型：选择/填空/解答
  "difficulty": 1-5,                 // 难度：1简单 2较易 3中等 4较难 5困难
  "estimated_time": number,          // 预计解题时间（分钟）
  "has_image": boolean,              // 是否包含图片
  "image_paths": ["string"],         // 图片路径数组（如有）
  
  "knowledge_points": ["string"],    // 知识点标签数组
  
  "content": "string",               // 题目内容（LaTeX 格式）
  
  "answer": {                        // 答案（根据题型调整结构）
    "part_I": "string",
    "part_II": "string"
  },
  
  "solution_steps": [                // 分步骤解析（用于AI教学）
    {
      "step_number": 1,
      "title": "string",             // 步骤标题
      "content": "string",           // 步骤内容
      "key_insight": "string"        // 关键思路
    }
  ],
  
  "teaching_guidance": [             // 教学引导（用于AI对话）
    {
      "step": 1,
      "prompt": "string",            // 引导问题
      "hint": "string",              // 提示
      "expected_answer": "string"    // 期望回答
    }
  ],
  
  "method_tags": ["string"],         // 解题方法标签
  "error_prone_points": ["string"],  // 易错点标签
  "feature_tags": ["string"],        // 题目特征标签
  
  "related_formulas": ["string"],    // 相关公式（LaTeX）
  "similar_questions": ["string"],   // 关联题目ID或描述
  
  "notes": {                         // 备注信息
    "status": "string",              // 题目状态：高考真题/模拟题/原创题
    "teaching_value": "string",      // 教学价值说明
    "common_difficulties": ["string"] // 学生常见困难
  }
}
```

---

## 🔄 题目整理 → 结构化流程

### Step 1: 组员整理题目（Markdown 格式）
每个组员按模板整理自己负责的题目，存放到：
```
knowledge_base/question/member_X/XXX_题号_题型_标题.md
```

### Step 2: 数据提取与转换
使用脚本将 Markdown 转换为 JSON：

```python
# scripts/convert_md_to_json.py
import os
import json
import re
import yaml

def parse_md_file(filepath):
    """解析单个 Markdown 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 YAML 元数据
    yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    metadata = yaml.safe_load(yaml_match.group(1)) if yaml_match else {}
    
    # 提取题目内容、解析等...
    # 返回结构化数据
    
    return {
        "id": metadata.get("id"),
        "source": metadata.get("source"),
        "type": metadata.get("type"),
        "difficulty": metadata.get("difficulty"),
        # ... 其他字段
    }

def batch_convert():
    """批量转换所有题目"""
    all_questions = []
    
    base_dir = "knowledge_base/question"
    for member_dir in os.listdir(base_dir):
        member_path = os.path.join(base_dir, member_dir)
        if os.path.isdir(member_path):
            for md_file in os.listdir(member_path):
                if md_file.endswith('.md'):
                    filepath = os.path.join(member_path, md_file)
                    question = parse_md_file(filepath)
                    all_questions.append(question)
    
    # 保存为单个 JSON 文件
    output = {
        "metadata": {
            "version": "1.0",
            "total_count": len(all_questions),
            "last_updated": datetime.now().isoformat()
        },
        "questions": all_questions
    }
    
    with open("backend/dataset/sequence_problems.json", 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    batch_convert()
```

### Step 3: 数据校验
```python
# scripts/validate_questions.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class QuestionModel(BaseModel):
    id: str = Field(..., pattern=r"^[A-E]_\d+$")
    source: str
    type: str = Field(..., pattern=r"^(选择|填空|解答)$")
    difficulty: int = Field(..., ge=1, le=5)
    knowledge_points: List[str]
    content: str
    
    @validator('knowledge_points')
    def check_knowledge_points(cls, v):
        if len(v) == 0:
            raise ValueError('知识点不能为空')
        return v

def validate_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for q in data['questions']:
        try:
            QuestionModel(**q)
            print(f"✅ {q['id']} 校验通过")
        except Exception as e:
            print(f"❌ {q['id']} 校验失败: {e}")
```

### Step 4: 构建向量索引
```python
# rag/build_index.py
import chromadb
from sentence_transformers import SentenceTransformer

def build_vector_index(questions_json_path):
    # 加载数据
    with open(questions_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 初始化 Chroma
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("sequence_questions")
    
    # 加载 Embedding 模型
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    
    # 批量添加
    for q in data['questions']:
        embedding = model.encode(q['content'])
        collection.add(
            ids=[q['id']],
            embeddings=[embedding.tolist()],
            metadatas=[{
                "difficulty": q['difficulty'],
                "type": q['type'],
                "knowledge_points": json.dumps(q['knowledge_points'])
            }],
            documents=[q['content']]
        )
    
    print(f"✅ 索引构建完成，共 {len(data['questions'])} 道题目")
```

---

## 📊 数据质量检查清单

在提交结构化数据前，请确认：

- [ ] **id 格式正确**：成员代号_序号（如 C_072）
- [ ] **知识点标签统一**：使用标准术语，如"裂项相消法"而非"裂项法"
- [ ] **难度合理**：1-5 的整数，与题目实际难度匹配
- [ ] **内容完整**：题目内容包含所有必要信息
- [ ] **步骤清晰**：solution_steps 逻辑连贯，易于理解
- [ ] **LaTeX 格式正确**：数学公式使用标准 LaTeX 语法
- [ ] **无敏感信息**：不包含个人隐私或版权风险内容

---

## 💡 最佳实践建议

1. **统一知识点词表**：建立标准知识点词典，避免同义词混乱
2. **定期备份**：JSON 文件纳入版本控制（Git）
3. **增量更新**：新增题目时，先更新 Markdown，再重新生成 JSON
4. **数据版本管理**：重大结构调整时，升级 version 字段
5. **团队协作**：使用 PR（Pull Request）机制审核题目质量

---

## 📁 文件目录结构（最终版）

```
AI Tutor/
├── backend/
│   ├── dataset/
│   │   ├── sequence_problems.json      # ⭐ 主数据文件（所有题目）
│   │   ├── question_template.json      # 题目模板示例
│   │   └── DATASET_README.md           # 本文档
│   └── rag/
│       └── build_index.py              # 构建向量索引脚本
├── knowledge_base/
│   └── question/                       # 原始 Markdown 文件
│       ├── member_A/
│       ├── member_B/
│       ├── member_C/
│       ├── member_D/
│       └── member_E/
└── scripts/
    ├── convert_md_to_json.py           # Markdown 转 JSON 脚本
    └── validate_questions.py           # 数据校验脚本
```

---

**总结**：推荐使用 **单个 JSON 文件** 存储所有题目，便于 RAG 检索、版本控制和团队协作。
