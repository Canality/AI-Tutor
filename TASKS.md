# AI Tutor 开发任务清单

> 创建时间: 2026-03-20
> 负责人: Lily (PM) + Main Agent (Dev)
> 项目路径: `D:\Project\AI Tutor`

---

## 🎯 本次迭代目标

根据用户需求，对 `learning_records` 表及相关逻辑进行架构级改进，支持双模态存储、A/B 测试追踪、JSON Schema 强校验。

---

## ✅ 任务分解

### Task 1: 模型层改进 - `models/record.py`

**需求**: 更新 LearningRecord 模型

**改动点**:
1. 新增字段 `recommendation_algorithm_version` (String, Nullable, Index)
2. 添加注释明确 `question_id` 和 `custom_question_data` 的互斥关系
3. 添加约束说明:
   - `source_type='uploaded'` → `question_id=None`, `custom_question_data` 必填
   - `source_type='recommended'/'practice'` → `question_id` 必填, `custom_question_data=None`

**代码参考**:
```python
# 新增字段
recommendation_algorithm_version = Column(String(50), nullable=True, index=True)
```

---

### Task 2: Schema 层创建 - `schemas/question.py` (新建文件)

**需求**: 创建 Pydantic 模型，严格定义上传题目的 JSON 结构

**需要定义的模型**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CustomQuestionPayload(BaseModel):
    """用户上传题目的标准结构 - 必须完全复刻 questions 表的核心字段"""
    content: str = Field(..., description="题目题干内容")
    standard_answer: Optional[str] = Field(None, description="标准答案")
    difficulty: int = Field(1, ge=1, le=3, description="难度等级: 1-简单, 2-中等, 3-困难")
    question_type: str = Field(..., description="题型: single_choice/multiple_choice/fill_blank")
    knowledge_points: List[str] = Field(default=[], description="知识点标签列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "解方程: 2x + 5 = 13",
                "standard_answer": "x = 4",
                "difficulty": 2,
                "question_type": "fill_blank",
                "knowledge_points": ["方程", "一元一次方程"]
            }
        }
```

**同时更新**: `schemas/__init__.py` 导出该模型

---

### Task 3: Service 层重构 - `services/record_service.py`

**需求**: 重写 `save_learning_record` 函数，加入双模态校验逻辑

**校验规则**:
```python
def validate_learning_record_data(
    source_type: str,
    question_id: Optional[int],
    custom_question_data: Optional[dict]
) -> None:
    """
    双模态存储校验:
    - uploaded: question_id 必须为 None, custom_question_data 必须存在且符合 Schema
    - recommended/practice: question_id 必须存在, custom_question_data 必须为 None
    """
    if source_type == 'uploaded':
        if question_id is not None:
            raise ValueError("用户上传题(source='uploaded')时 question_id 必须为 None")
        if not custom_question_data:
            raise ValueError("用户上传题必须提供 custom_question_data")
        # 使用 Pydantic 验证
        CustomQuestionPayload(**custom_question_data)
    elif source_type in ('recommended', 'practice'):
        if question_id is None:
            raise ValueError(f"系统推荐题(source='{source_type}')时 question_id 不能为空")
        if custom_question_data is not None:
            raise ValueError(f"系统推荐题(source='{source_type}')时 custom_question_data 必须为 None")
    else:
        raise ValueError(f"未知的 source_type: {source_type}")
```

**函数签名更新**:
```python
async def save_learning_record(
    db: AsyncSession,
    user_id: int,
    question_obj: Question = None,
    custom_question_data: dict = None,  # 改为 dict，不再是简单字符串
    answer: str = "",
    is_correct: bool = None,
    source_type: str = 'recommended',
    recommendation_algorithm_version: str = None,  # 新增参数
    recommendation_session_id: str = None  # 已有，确保传入
)
```

---

### Task 4: 推荐服务更新 - `services/recommendation_service.py`

**需求**: 在创建 LearningRecord 时写入 algorithm_version

**改动点**:
1. 函数签名增加 `algorithm_version` 参数
2. 在返回推荐列表时，包含 `algorithm_version` 信息
3. 调用方需要传递版本号

**示例**:
```python
# 在 recommend_exercises 函数中
recommended_list = []
algorithm_version = "rule_v1"  # 或从配置读取

for q in final_questions:
    recommended_list.append({
        "id": q.id,
        "type": q.question_type,
        "content": q.content,
        "difficulty": q.difficulty,
        "knowledge_points": q.knowledge_points or [],
        "image_url": None,
        "algorithm_version": algorithm_version  # 新增
    })
```

---

### Task 5: 掌握度算法架构 - `services/profile_service.py`

**需求**: 创建策略模式预留接口

**新增代码**:
```python
from typing import Dict, List, Callable
from models.record import LearningRecord

# 策略函数类型定义
MasteryStrategy = Callable[[List[LearningRecord]], Dict[str, float]]

def calculate_mastery_simple(records: List[LearningRecord]) -> Dict[str, float]:
    """
    V1: 简单正确率算法
    mastery = correct_count / total_count
    """
    topic_stats = {}
    
    for record in records:
        # 获取知识点列表
        if record.source_type == 'uploaded':
            topics = record.custom_question_data.get('knowledge_points', ['未知']) if record.custom_question_data else ['未知']
        else:
            topics = record.question.knowledge_points if record.question else ['未知']
            if isinstance(topics, str):
                import json
                topics = json.loads(topics)
        
        for topic in topics:
            if topic not in topic_stats:
                topic_stats[topic] = {'total': 0, 'correct': 0}
            topic_stats[topic]['total'] += 1
            if record.is_correct:
                topic_stats[topic]['correct'] += 1
    
    # 计算掌握度
    mastery = {}
    for topic, stats in topic_stats.items():
        mastery[topic] = round(stats['correct'] / stats['total'], 2) if stats['total'] > 0 else 0.0
    
    return mastery

async def calculate_mastery_score(
    db: AsyncSession,
    user_id: int,
    strategy: str = "simple"
) -> Dict[str, float]:
    """
    计算用户知识点掌握度 - 策略模式入口
    
    Args:
        strategy: 算法策略名称
            - "simple": 简单正确率 (V1)
            - "weighted_time_decay": 时间加权衰减 (V2, 待实现)
    
    Returns:
        Dict[知识点, 掌握度分数]
    """
    # 获取用户学习记录
    from sqlalchemy import select
    stmt = select(LearningRecord).where(LearningRecord.user_id == user_id)
    result = await db.execute(stmt)
    records = result.scalars().all()
    
    # 策略映射表
    strategies: Dict[str, MasteryStrategy] = {
        "simple": calculate_mastery_simple,
        # "weighted_time_decay": calculate_mastery_weighted,  # V2 预留
    }
    
    if strategy not in strategies:
        raise ValueError(f"未知的掌握度算法策略: {strategy}")
    
    return strategies[strategy](records)
```

---

### Task 6: API 层更新

**需要检查并更新的 API 端点**:
1. `api/exercises.py` - 保存学习记录时传入 algorithm_version
2. `api/upload.py` - 用户上传题目时使用 CustomQuestionPayload 校验

---

### Task 7: 数据库文档更新

**更新**: `D:\Computer\openclaw\AI_Tutor_数据库表结构文档.md`

**修改内容**:
1. 更新 `learning_records` 表结构说明
2. 明确 `custom_question_data` 是"虚拟题目"的完整结构化存储
3. 添加 `recommendation_algorithm_version` 字段说明

---

## 📝 开发顺序建议

```
Task 1 (模型) → Task 2 (Schema) → Task 3 (Service层校验) → Task 4 (推荐服务) → Task 5 (掌握度) → Task 6 (API) → Task 7 (文档)
```

---

## 🔍 代码审查检查点

每个 Task 完成后，请确认:

- [ ] **Task 1**: 数据库迁移脚本是否需要更新？
- [ ] **Task 2**: Pydantic 模型字段与 `questions` 表完全对应？
- [ ] **Task 3**: 互斥校验逻辑覆盖所有分支？
- [ ] **Task 4**: algorithm_version 正确传递到 LearningRecord？
- [ ] **Task 5**: 策略函数接口统一，易于扩展？
- [ ] **Task 6**: API 测试通过，无 500 错误？
- [ ] **Task 7**: 文档与实际代码一致？

---

## 💡 额外建议

1. **数据库迁移**: 如果项目使用 Alembic，需要生成迁移脚本添加新字段
2. **向后兼容**: 现有数据如何处理？建议:
   - `recommendation_algorithm_version` 默认为 NULL
   - 现有 `custom_question_data` 需要数据清洗
3. **测试**: 建议为 `validate_learning_record_data` 编写单元测试

---

**下一步**: Main Agent 请从 Task 1 开始，逐个完成并在此文档中打勾确认。
