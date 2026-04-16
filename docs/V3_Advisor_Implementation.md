# Advisor Agent 指令集实现文档

**需求来源**: PRD文档3.2节 - Advisor Agent 指令集  
**状态**: ✅ 已完成  
**完成日期**: 2026-04-16  
**遵循标准**: 所有参数均为PRD定义的硬指标（Baseline）

---

## 实现概述

严格遵循PRD文档3.2节硬指标，实现Advisor Agent指令集：

| 指令编码 | 指令名称 | 触发条件 | 控制参数 | 状态 |
|---------|---------|---------|---------|------|
| MODE_SCAFFOLD | 脚手架模式 | P(L) < 0.4 或 连续2题错误 | detailed, step_by_step, allow_skip | ✅ |
| MODE_CHALLENGE | 挑战模式 | P(L) > 0.8 且 近期正确率高 | minimal, step_by_step, allow_skip | ✅ |
| MODE_ENCOURAGE | 鼓励模式 | 连续3题错误或表达挫败感 | adaptive, step_by_step, encouragement | ✅ |
| MODE_NORMAL | 正常模式 | 默认 | standard | ✅ |

---

## 1. 指令定义（硬指标）

### 1.1 MODE_SCAFFOLD（脚手架模式）

**触发条件**（硬指标）：
- P(L) < 0.4
- 或 连续2题错误

**控制参数**（硬指标）：
```json
{
  "hint_level": "detailed",
  "max_hints": 5,
  "step_by_step": true,
  "allow_skip": true,
  "estimated_steps": 4,
  "confirm_each_step": true
}
```

**Instructor行为约束**（硬指标）：
- 必须分步讲解
- 每步后确认理解
- 允许随时请求提示

### 1.2 MODE_CHALLENGE（挑战模式）

**触发条件**（硬指标）：
- P(L) > 0.8
- 且 近期正确率高

**控制参数**（硬指标）：
```json
{
  "hint_level": "minimal",
  "max_hints": 2,
  "step_by_step": false,
  "allow_skip": false,
  "show_full_solution": false
}
```

**Instructor行为约束**（硬指标）：
- 仅给出方向性提示
- 要求学生自主推导
- 不展开中间步骤

### 1.3 MODE_ENCOURAGE（鼓励模式）

**触发条件**（硬指标）：
- 连续3题错误
- 或 主动表达挫败感

**控制参数**（硬指标）：
```json
{
  "hint_level": "adaptive",
  "max_hints": 10,
  "step_by_step": true,
  "encouragement": true,
  "positive_reinforcement": true,
  "error_framing": "learning_opportunity"
}
```

**Instructor行为约束**（硬指标）：
- 先给予情感支持
- 再逐步引导
- 强调"错误是学习机会"

---

## 2. 指令下发格式（硬指标）

```json
{
  "instruction": "MODE_SCAFFOLD",
  "reasoning": "学生在等比数列知识点掌握度仅为0.35,需要分步引导",
  "control_params": {
    "hint_level": "detailed",
    "max_hints": 5,
    "step_by_step": true,
    "estimated_steps": 4
  },
  "instructor_prompt": "请使用苏格拉底式提问,分4步引导学生理解等比数列求和公式的推导..."
}
```

---

## 3. 实现代码

### 3.1 核心类

**文件**: `backend/agents/advisor_agent.py`

```python
class AdvisorAgent:
    """Advisor Agent核心类"""
    
    # 硬指标阈值
    SCAFFOLD_THRESHOLD = 0.4        # 脚手架模式阈值
    CHALLENGE_THRESHOLD = 0.8       # 挑战模式阈值
    CONSECUTIVE_WRONG_THRESHOLD = 2 # 连续错误阈值（脚手架）
    CONSECUTIVE_WRONG_ENCOURAGE = 3 # 连续错误阈值（鼓励）
    RECENT_ACCURACY_THRESHOLD = 0.7 # 近期正确率阈值
    
    def determine_mode(self, state: UserLearningState) -> AdvisorMode:
        """判断教学模式（硬指标）"""
        # 鼓励模式（最高优先级）
        if (state.consecutive_wrong >= self.CONSECUTIVE_WRONG_ENCOURAGE or 
            state.recent_sentiment in ["frustrated", "discouraged"]):
            return AdvisorMode.ENCOURAGE
        
        # 脚手架模式
        if (state.p_known < self.SCAFFOLD_THRESHOLD or 
            state.consecutive_wrong >= self.CONSECUTIVE_WRONG_THRESHOLD):
            return AdvisorMode.SCAFFOLD
        
        # 挑战模式
        if (state.p_known > self.CHALLENGE_THRESHOLD and 
            state.recent_accuracy > self.RECENT_ACCURACY_THRESHOLD):
            return AdvisorMode.CHALLENGE
        
        # 正常模式
        return AdvisorMode.NORMAL
```

### 3.2 模式判定优先级

```
1. 鼓励模式（最高优先级）
   └─ 连续3题错误 或 表达挫败感

2. 脚手架模式
   └─ P(L) < 0.4 或 连续2题错误

3. 挑战模式
   └─ P(L) > 0.8 且 近期正确率高

4. 正常模式（默认）
   └─ 以上条件都不满足
```

---

## 4. API接口

### 4.1 生成Advisor指令

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/advisor/instruction` | 根据用户状态生成指令 |

**请求示例**：
```json
{
  "user_id": 1,
  "theta": 0.0,
  "p_known": 0.35,
  "consecutive_correct": 0,
  "consecutive_wrong": 2,
  "recent_accuracy": 0.4,
  "weak_knowledge_points": [["等比数列", 35]]
}
```

**响应示例**：
```json
{
  "instruction": "MODE_SCAFFOLD",
  "reasoning": "学生在【等比数列】知识点掌握度仅为0.35，需要分步引导",
  "control_params": {
    "hint_level": "detailed",
    "max_hints": 5,
    "step_by_step": true,
    "allow_skip": true,
    "estimated_steps": 4,
    "confirm_each_step": true
  },
  "instructor_prompt": "请使用苏格拉底式提问，分4步引导学生理解..."
}
```

### 4.2 检查当前模式

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/advisor/mode/check` | 检查当前教学模式 |

### 4.3 生成推荐理由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/advisor/recommendation/reason` | 生成题目推荐理由 |

---

## 5. 验收标准

### 5.1 功能验收

```python
# 测试用例1: 脚手架模式
state1 = UserLearningState(
    p_known=0.35,  # < 0.4
    consecutive_wrong=2
)
mode1 = advisor.determine_mode(state1)
assert mode1 == AdvisorMode.SCAFFOLD

# 测试用例2: 挑战模式
state2 = UserLearningState(
    p_known=0.85,  # > 0.8
    recent_accuracy=0.85  # > 0.7
)
mode2 = advisor.determine_mode(state2)
assert mode2 == AdvisorMode.CHALLENGE

# 测试用例3: 鼓励模式
state3 = UserLearningState(
    consecutive_wrong=3  # 连续3题错误
)
mode3 = advisor.determine_mode(state3)
assert mode3 == AdvisorMode.ENCOURAGE
```

### 5.2 PRD符合度检查

| 检查项 | PRD要求 | 实现状态 |
|--------|---------|---------|
| 脚手架触发条件 | P(L) < 0.4 或 连续2题错误 | ✅ |
| 挑战触发条件 | P(L) > 0.8 且 近期正确率高 | ✅ |
| 鼓励触发条件 | 连续3题错误或表达挫败感 | ✅ |
| 指令格式 | 包含instruction/reasoning/control_params/instructor_prompt | ✅ |
| 控制参数 | 符合各模式的硬指标 | ✅ |

---

## 6. 代码统计

| 模块 | 文件 | 代码行数 |
|------|------|---------|
| Agent层 | `agents/advisor_agent.py` | 400+ |
| API层 | `api/advisor_api.py` | 350+ |
| 文档 | `docs/V3_Advisor_Implementation.md` | 200+ |
| **总计** | - | **950+行** |

---

## 7. 下一步工作

1. **集成Instructor Agent** - 接收Advisor指令并执行
2. **实现触发机制** - 主动/被动/定时触发
3. **完善推荐理由生成** - 结合RAG候选池

---

## 8. 附录：触发场景（PRD 3.1.1节）

| 触发类型 | 触发条件 | 预处理动作 |
|---------|---------|-----------|
| 主动请求 | 学生点击"推荐题目" | 读取完整画像，执行完整推荐流程 |
| 被动触发 | 当前题目完成后自动触发 | 快速读取Redis缓存，执行轻量推荐 |
| 定时触发 | 每日学习提醒 | 基于历史数据生成日计划 |
