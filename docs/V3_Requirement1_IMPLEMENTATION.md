# 需求1实现文档：基于连对/连错状态的实时UI交互与难度自适应调整

**需求编号**：1  
**需求名称**：基于连对/连错状态的实时UI交互与难度自适应调整  
**优先级**：P0  
**状态**：✅ 已完成  
**完成日期**：2026-04-16  

---

## 需求概述

### 核心逻辑
- **高光连击**：连续正确3次，触发难度上限 $S_{next}$ 提升0.3。UI弹出火焰图标连击特效，Advisor发出激励话术。
- **降级保护**：连续错误2次，触发难度下限 $S_{next}$ 降低0.3。UI弹出保护伞/咖啡杯动效，Advisor发出降压引导话术。

### PRD硬指标
| 参数 | 值 | 说明 |
|------|-----|------|
| 高光连击阈值 | 3次 | 连续正确3次触发 |
| 降级保护阈值 | 2次 | 连续错误2次触发 |
| 难度调整幅度 | ±0.3 | 上限+0.3或下限-0.3 |
| 基础难度范围 | [θ-0.5, θ+0.5] | 基于能力值的推荐范围 |

---

## 实现文件

### 1. 算法层
**文件**：`backend/algorithms/streak_handler.py` (350+行)

**核心类**：
- `StreakHandler` - 连击处理器主类
- `StreakState` - 连击状态数据类
- `DifficultyAdjustment` - 难度调整结果类
- `UIEffect` - UI效果定义类

**关键方法**：
```python
# 更新连击状态
update_streak(user_id, is_correct) -> StreakState

# 检查是否触发效果
check_streak_effect(user_id) -> (StreakEffect, streak_count)

# 计算难度调整范围
calculate_difficulty_range(user_id, theta) -> DifficultyAdjustment

# 获取UI效果
get_ui_effect(user_id) -> UIEffect

# 处理答题（整合以上所有功能）
process_answer(user_id, is_correct, theta) -> Dict
```

### 2. 服务层
**文件**：`backend/services/cognitive_diagnosis_service.py`

**修改内容**：
- 添加 `streak_handler` 实例
- 修改 `update_knowledge_mastery()` 方法，返回包含连击状态的完整结果

### 3. API层
**文件**：`backend/api/cognitive_diagnosis.py`

**新增端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/cognitive/streak/update` | 更新连击状态并触发难度调整 |
| GET | `/api/cognitive/streak/state/{user_id}` | 获取用户当前连击状态 |
| POST | `/api/cognitive/streak/reset/{user_id}` | 重置用户连击状态 |

### 4. Mock服务器
**文件**：`backend/mock_server_simple.py`

**Mock端点**：
- `POST /api/cognitive/streak/update` - 模拟连击更新

---

## API使用示例

### 更新连击状态
```bash
curl -X POST http://localhost:8000/api/cognitive/streak/update \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "knowledge_point_id": 101,
    "is_correct": true
  }'
```

**响应示例**（连续答对3次后）：
```json
{
  "user_id": 1,
  "knowledge_point_id": 101,
  "p_known": 0.8727,
  "p_known_change": 0.0727,
  "consecutive_correct": 3,
  "consecutive_wrong": 0,
  "difficulty_adjustment": {
    "original_range": "[0.00, 1.00]",
    "adjusted_range": "[0.00, 1.30]",
    "adjustment_delta": 0.3,
    "effect_type": "highlight",
    "effect_triggered": true,
    "streak_count": 3
  },
  "ui_effect": {
    "effect_type": "highlight",
    "icon": "fire",
    "animation": "flame_burst",
    "advisor_message": "太棒了！你已经连续答对3题，继续保持这个势头！",
    "color_theme": "orange",
    "streak_count": 3
  },
  "should_trigger_effect": true
}
```

### 获取连击状态
```bash
curl http://localhost:8000/api/cognitive/streak/state/1
```

**响应示例**：
```json
{
  "user_id": 1,
  "consecutive_correct": 3,
  "consecutive_wrong": 0,
  "current_streak_type": "win",
  "current_streak_count": 3
}
```

---

## 算法测试结果

```
=== 测试1：连续答对3次（触发高光连击）===
  第1次答对: 难度范围 [0.00, 1.00]
  第2次答对: 难度范围 [0.00, 1.00]
  第3次答对: 难度范围 [0.00, 1.30] ✓ 上限+0.3
             -> 触发UI效果: fire (highlight)

=== 测试2：连续答错2次（触发降级保护）===
  第1次答错: 难度范围 [0.00, 1.00]
  第2次答错: 难度范围 [-0.30, 1.00] ✓ 下限-0.3
             -> 触发UI效果: shield (downgrade_protection)
```

---

## 前端集成指南

### 1. 答题后调用API
```javascript
// 学生提交答案后
const response = await fetch('/api/cognitive/streak/update', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    knowledge_point_id: kpId,
    is_correct: isCorrect
  })
});

const result = await response.json();

// 检查是否触发UI效果
if (result.should_trigger_effect) {
  showUIEffect(result.ui_effect);
}

// 更新推荐难度范围
updateDifficultyRange(result.difficulty_adjustment.adjusted_range);
```

### 2. 显示UI效果
```javascript
function showUIEffect(uiEffect) {
  // 显示图标动画
  showIconAnimation(uiEffect.icon, uiEffect.animation);
  
  // 显示Advisor话术
  showAdvisorMessage(uiEffect.advisor_message);
  
  // 应用颜色主题
  applyColorTheme(uiEffect.color_theme);
}
```

### 3. UI效果定义

| 效果类型 | 图标 | 动画 | 颜色主题 | Advisor话术 |
|---------|------|------|---------|------------|
| highlight | fire | flame_burst | orange | "太棒了！你已经连续答对{N}题，继续保持这个势头！" |
| downgrade_protection | shield | gentle_fade | blue | "别灰心，这道题确实有些挑战。我们先降低难度，打好基础再回来攻克它！" |

---

## 代码统计

| 模块 | 文件 | 代码行数 |
|------|------|---------|
| 算法层 | `algorithms/streak_handler.py` | 350+ |
| 服务层 | `services/cognitive_diagnosis_service.py` | 修改50+ |
| API层 | `api/cognitive_diagnosis.py` | 新增150+ |
| Mock层 | `mock_server_simple.py` | 新增80+ |
| 测试 | `test_streak_api.py` | 200+ |
| **总计** | - | **830+行** |

---

## 下一步工作

1. **前端对接** - 集成UI效果显示
2. **需求10** - 游戏技能树展示知识点依赖关系
3. **需求16** - 渐进式提示按钮（单一按钮L0-L4）

---

## 备注

- 所有参数严格遵循PRD文档，为硬指标
- 难度范围限制在[-3, +3]之间（IRT标准范围）
- UI效果文案支持动态替换连击数
- Mock服务器已更新，前端可立即开始对接
