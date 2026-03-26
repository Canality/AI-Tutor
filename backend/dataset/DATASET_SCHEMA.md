# AI Tutor 知识库数据格式规范

## 📁 文件存储方案

### 推荐方案：一个题目一个JSON文件

**原因：**
1. **便于管理** - 单个文件损坏不影响其他题目
2. **便于协作** - 多人同时编辑不同题目不会冲突
3. **便于版本控制** - Git可以追踪每个题目的修改历史
4. **便于检索** - 按ID快速定位文件
5. **便于扩展** - 新增题目只需添加新文件

### 文件目录结构

```
backend/dataset/
├── questions/                    # 题目数据文件夹
│   ├── C_072.json               # member C - page 72
│   ├── E_125.json               # member E - page 125
│   ├── E_126.json
│   └── ...
├── index.json                   # 数据集索引（自动生成）
├── question_template.json       # 题目模板示例
├── md_to_json_converter.py      # Markdown转JSON脚本
└── DATASET_README.md           # 本文档
```

## 📋 JSON数据结构规范

### 顶层字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | string | ✓ | 题目唯一标识，格式：成员代号_页码（如E_125） |
| source | string | ✓ | 题目来源，格式：书名P页码 题号 |
| type | string | ✓ | 题型：选择/填空/解答 |
| difficulty | integer | ✓ | 难度等级：1-5 |
| estimated_time | integer | ✓ | 预计解题时间（分钟） |
| has_image | boolean | ✓ | 是否包含图片 |
| image_paths | array | ✓ | 图片路径数组（空数组表示无图片） |
| knowledge_points | array | ✓ | 知识点标签数组 |
| content | string | ✓ | 题目内容（纯文本，LaTeX已转换） |
| parts | array | ✗ | 多问题目的各部分 |
| solution_steps | array | ✓ | 详细解题步骤 |
| teaching_guidance | array | ✓ | AI教学引导 |
| method_tags | array | ✓ | 解题方法标签 |
| error_prone_points | array | ✓ | 易错点标签 |
| feature_tags | array | ✓ | 题目特征标签 |
| related_formulas | array | ✗ | 相关公式 |
| similar_questions | array | ✗ | 类似题目推荐 |
| notes | object | ✓ | 备注信息 |
| metadata | object | ✓ | 元数据（创建者、时间等） |

### 详细字段说明

#### parts（题目各部分）

```json
{
  "part_id": "main",           // 部分标识：main/I/II/III
  "title": "证明不等式",        // 部分标题
  "answer": "证明见解析",        // 答案
  "solution": "详细解析..."     // 解析内容
}
```

#### solution_steps（解题步骤）

```json
{
  "step_number": 1,            // 步骤序号
  "title": "分析通项",          // 步骤标题
  "content": "需要证明...",      // 步骤内容
  "key_insight": "关键观察..."  // 关键洞察
}
```

#### teaching_guidance（教学引导）

```json
{
  "step": 1,                   // 对应解题步骤
  "prompt": "引导语...",        // AI引导语
  "hint": "提示...",            // 关键提示（可选）
  "expected_answer": "期望回答" // 期望学生回答
}
```

#### notes（备注）

```json
{
  "status": "经典例题",         // 题目地位
  "teaching_value": "教学价值...", // 教学价值说明
  "common_difficulties": [      // 学生常见困难
    "困难1",
    "困难2"
  ],
  "recommended_teaching_order": "建议教学顺序"
}
```

#### metadata（元数据）

```json
{
  "created_by": "组员E",        // 创建者
  "created_at": "2026-03-26",   // 创建时间
  "page": 125,                  // 页码
  "book": "《新高考你真的掌握了吗？·数列》"  // 书名
}
```

## 🔄 Markdown转JSON工作流程

### 1. 整理Markdown题目
按照模板格式整理每道题目，保存为 `.md` 文件。

### 2. 运行转换脚本
```bash
cd backend/dataset
python md_to_json_converter.py
```

脚本会自动：
- 解析Markdown文件
- 提取元数据、题目内容、解析步骤等
- 生成对应的JSON文件
- 更新索引文件 `index.json`

### 3. 验证JSON文件
检查生成的JSON文件是否符合规范。

### 4. 提交到GitHub
```bash
git add questions/
git add index.json
git commit -m "Add questions for member E (pages 125-144)"
git push
```

## 📊 索引文件结构

`index.json` 自动生成，包含：

```json
{
  "version": "1.0",
  "total_questions": 27,
  "members": {
    "C": ["C_072"],
    "E": ["E_125", "E_126", "..."]
  },
  "statistics": {
    "by_difficulty": {
      "3": 10,
      "4": 12,
      "5": 5
    },
    "by_type": {
      "解答": 27
    },
    "by_knowledge_point": {
      "裂项放缩法": 8,
      "递推数列": 6,
      "...": "..."
    }
  }
}
```

## 🛠️ 开发工具

### md_to_json_converter.py
批量转换Markdown文件为JSON格式。

**使用方法：**
```python
# 转换单个文件
from md_to_json_converter import convert_md_to_json
convert_md_to_json("path/to/question.md", "path/to/output/")

# 批量转换
from md_to_json_converter import batch_convert
batch_convert("knowledge_base/question/member_E/", "backend/dataset/questions/")

# 生成索引
from md_to_json_converter import generate_dataset_index
generate_dataset_index("backend/dataset/")
```

## 📝 命名规范

### Markdown文件命名
```
{页码}_{题号}_{题型}_{简要描述}.md

示例：
125_例5.10_解答_裂项放缩法证明不等式.md
128_变式5.13.2_解答_双曲线与递推数列综合题.md
```

### JSON文件命名
```
{ID}.json

示例：
E_125.json
C_072.json
```

## ✅ 质量检查清单

提交前请确认：

- [ ] JSON文件格式正确（可用JSON validator检查）
- [ ] 所有必填字段已填写
- [ ] id格式正确（成员代号_页码）
- [ ] difficulty在1-5范围内
- [ ] knowledge_points不为空
- [ ] solution_steps和teaching_guidance步骤对应
- [ ] 索引文件已更新

## 🔗 相关文档

- `question_template.json` - 完整模板示例
- `E_125.json` - 示例题目数据
- `DATASET_README.md` - 数据集说明（本文档）
