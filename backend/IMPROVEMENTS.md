# AI Tutor 项目代码改进文档

> 本文档详细说明了基于产品经理需求文档进行的代码改进内容。

---

## 📋 改进概览

| 改进点 | 涉及文件 | 优先级 |
|--------|----------|--------|
| 双模态存储逻辑 | `models/record.py`, `services/record_service.py` | 🚨 高 |
| A/B 测试支持 | `models/record.py`, `services/recommendation_service.py` | 🚀 高 |
| JSON Schema 验证 | `schemas/question.py` | 🧠 高 |
| 掌握度算法预留接口 | `services/profile_service.py` | 📊 中 |

---

## 🚨 修正点 1：双模态存储逻辑

### 问题背景

原有的 `learning_records` 表设计允许 `question_id` 和 `custom_question_data` 同时存在或同时为空，这会导致数据不一致和查询困难。

### 解决方案

引入**双模态存储设计**，两种模式互斥：

#### 模式 A：系统题库题
- **适用场景**: 用户使用系统推荐的题目或随机练习题
- **source_type**: `'recommended'` 或 `'practice'`
- **字段要求**:
  - `question_id`: **必填** (外键关联 `questions.id`)
  - `custom_question_data`: **必须为 NULL**
  - `is_correct`: **必填** (布尔值)

#### 模式 B：用户上传题
- **适用场景**: 用户上传自己的题目（图片/文本）
- **source_type**: `'uploaded'`
- **字段要求**:
  - `question_id`: **必须为 NULL**
  - `custom_question_data`: **必填** (JSON 格式)
  - `is_correct`: **可空** (用户上传题可能无标准答案)

### 代码修改

#### 1. `models/record.py`

**新增内容**:
- 添加了详细的类级文档字符串，说明双模态设计原则
- 添加了 JSON Schema 约束说明
- 更新了字段注释，明确互斥关系

```python
class LearningRecord(Base):
    """
    学习记录模型 - 双模态存储设计

    【核心设计原则 - 双模态互斥关系】
    ========================================
    本模型支持两种互斥的数据存储模式...
    """
```

#### 2. `services/record_service.py` (完全重写)

**新增功能**:
- `save_learning_record()`: 核心保存函数，包含严格的双模态校验逻辑
- `save_uploaded_question_record()`: 模式 B 的便捷方法
- `save_recommended_question_record()`: 模式 A 的便捷方法
- `extract_question_data()`: 统一提取题目数据的工具函数

**校验逻辑示例**:
```python
if source_type in ('recommended', 'practice'):
    if question_obj is None:
        raise RecordValidationError("模式 A 要求提供 question_obj")
    if custom_question_payload is not None:
        raise RecordValidationError("模式 A 不允许提供 custom_question_payload")
elif source_type == 'uploaded':
    if question_obj is not None:
        raise RecordValidationError("模式 B 不允许提供 question_obj")
    if custom_question_payload is None:
        raise RecordValidationError("模式 B 要求提供 custom_question_payload")
```

---

## 🚀 改进点 2：A/B 测试支持

### 问题背景

原有的推荐系统无法追踪不同算法版本的效果，无法进行科学的 A/B 测试。

### 解决方案

1. **数据库层**: 新增 `recommendation_algorithm_version` 字段
2. **服务层**: 推荐函数支持传入算法版本参数
3. **记录层**: 保存学习记录时记录算法版本

### 代码修改

#### 1. `models/record.py`

**新增字段**:
```python
# --- A/B 测试支持: 推荐算法版本 ---
recommendation_algorithm_version = Column(
    String(50),
    nullable=True,
    index=True,
    comment="用于记录生成此推荐的算法版本，支持 A/B 测试"
)
```

#### 2. `services/recommendation_service.py` (完全重写)

**新增功能**:
- 算法版本常量定义 (`v1.0`, `v2.0`, `control`, `treatment`)
- `recommend_exercises()`: 支持 `algorithm_version` 参数
- `_sort_topics_v1()`: 基础排序策略（按错误次数）
- `_sort_topics_v2()`: 实验排序策略（综合错误次数和掌握度）
- `record_recommendation_result()`: 保存推荐答题结果
- `get_recommendation_ab_test_stats()`: 获取 A/B 测试统计数据

**使用示例**:
```python
# 获取推荐（使用实验版本）
recommendations = await recommend_exercises(
    db=db,
    user_id=user_id,
    limit=5,
    algorithm_version="v2.0"  # A/B 测试
)

# 保存答题结果（自动记录算法版本）
record = await record_recommendation_result(
    db=db,
    user_id=user_id,
    question_id=question_id,
    user_answer=answer,
    is_correct=is_correct,
    algorithm_version="v2.0"
)
```

---

## 🧠 改进点 3：JSON Schema 验证

### 问题背景

原有的 `custom_question_data` 字段缺乏结构约束，可能导致数据不一致。

### 解决方案

使用 Pydantic 模型定义严格的 JSON Schema，在 API 层自动校验。

### 代码修改

#### 1. 新建 `schemas/question.py`

**定义两个核心模型**:

##### `CustomQuestionData`
用于存储在 `learning_records.custom_question_data` 中的数据。

```python
class CustomQuestionData(BaseModel):
    content: str                    # 题目内容，必填
    standard_answer: Optional[str]  # 标准答案，可选
    difficulty: int                 # 难度 1-5，默认 2
    question_type: Literal[...]     # 题型枚举
    knowledge_points: List[str]     # 知识点标签
```

##### `CustomQuestionPayload`
用于 API 层接收用户上传的题目数据。

```python
class CustomQuestionPayload(BaseModel):
    content: str                    # 题目内容
    standard_answer: Optional[str]  # 标准答案
    difficulty: int                 # 难度
    question_type: Literal[...]     # 题型
    knowledge_points: List[str]     # 知识点
    user_answer: str                # 用户答案

    def to_custom_question_data(self) -> CustomQuestionData:
        # 转换为存储格式（去除 user_answer）
```

**校验规则**:
- `content`: 1-10000 字符，自动去除首尾空白
- `difficulty`: 1-5 整数
- `knowledge_points`: 最多 20 个，自动去重去空
- `user_answer`: 1-10000 字符

#### 2. `schemas/__init__.py`

导出新的 Schema:
```python
from schemas.question import (
    CustomQuestionData,
    CustomQuestionPayload,
    QuestionResponse
)
```

#### 3. API 层使用示例 (`api/records_example.py`)

展示了如何在 FastAPI 路由中使用新的 Schema:

```python
@router.post("/upload")
async def upload_question_record(
    payload: CustomQuestionPayload,  # FastAPI 自动校验
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    # payload 已通过 Schema 校验
    record = await save_uploaded_question_record(
        db=db,
        user_id=user_id,
        payload=payload
    )
```

---

## 📊 额外建议：掌握度算法预留接口

### 问题背景

原有的掌握度计算逻辑单一，无法支持未来更复杂的算法。

### 解决方案

引入策略模式，支持多种掌握度计算策略。

### 代码修改

#### `services/profile_service.py` (完全重写)

**新增策略函数**:

##### `calculate_mastery_score()`
统一的掌握度计算入口，支持策略选择。

```python
def calculate_mastery_score(
    records: List[LearningRecord],
    strategy: Literal["simple", "weighted_time_decay", "exponential_smoothing"] = "simple",
    current_time: Optional[datetime] = None
) -> Dict[str, float]:
    """计算知识点掌握度分数 - 策略模式实现"""
```

**支持的策略**:

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `simple` | 简单平均，计算正确率 | 基础场景 |
| `weighted_time_decay` | 时间衰减加权，近期答题权重更高 | 关注学习进步 |
| `exponential_smoothing` | 指数平滑，更关注近期表现 | 快速响应变化 |

**策略实现示例** (`weighted_time_decay`):
```python
def _calculate_mastery_weighted_time_decay(records, current_time, decay_half_life_days=7.0):
    # 半衰期默认为 7 天
    lambda_decay = 0.693 / decay_half_life_days

    for record in records:
        days_diff = (current_time - record.created_at).days
        weight = 2.718 ** (-lambda_decay * days_diff)  # 时间权重
        # 加权计算掌握度...
```

**新增服务函数**:
```python
async def get_user_profile_with_mastery(
    db: AsyncSession,
    user_id: int,
    mastery_strategy: str = "simple"
) -> Dict:
    """获取用户画像（包含动态计算的掌握度）"""
```

---

## 📁 文件变更清单

### 修改的文件

| 文件路径 | 变更类型 | 说明 |
|----------|----------|------|
| `models/record.py` | 修改 | 添加双模态注释和 A/B 测试字段 |
| `services/record_service.py` | 重写 | 实现双模态校验逻辑 |
| `services/recommendation_service.py` | 重写 | 添加 A/B 测试支持 |
| `services/profile_service.py` | 重写 | 添加掌握度策略模式 |
| `schemas/__init__.py` | 修改 | 导出新的 Schema |

### 新建的文件

| 文件路径 | 说明 |
|----------|------|
| `schemas/question.py` | 题目相关的 Pydantic Schema |
| `api/records_example.py` | API 层使用示例代码 |

---

## 🔧 后续建议

### 数据库迁移

需要执行以下 SQL 迁移脚本添加新字段：

```sql
-- 添加 A/B 测试字段
ALTER TABLE learning_records
ADD COLUMN recommendation_algorithm_version VARCHAR(50) NULL,
ADD INDEX idx_learning_records_algorithm_version (recommendation_algorithm_version);

-- 更新字段注释
ALTER TABLE learning_records
MODIFY COLUMN question_id INT NULL COMMENT '模式 A 必填，模式 B 为 NULL',
MODIFY COLUMN custom_question_data JSON NULL COMMENT '模式 B 必填，模式 A 为 NULL';
```

### 集成到现有 API

建议将 `api/records_example.py` 中的代码整合到现有的路由文件中：
1. 复制路由函数到 `api/exercises.py` 或新建 `api/records.py`
2. 更新 `main.py` 中的路由注册
3. 添加 JWT 认证依赖

### 测试建议

1. **单元测试**: 测试双模态校验逻辑的各种边界情况
2. **集成测试**: 测试完整的推荐-答题-记录流程
3. **A/B 测试**: 对比不同算法版本的效果指标

---

## 📞 技术支持

如有疑问，请联系开发团队。

---

*文档生成时间: 2026-03-20*
