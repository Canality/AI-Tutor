# 需求16实现文档：渐进式提示按钮 - 动态折叠交互状态机

**需求编号**：16  
**需求名称**：渐进式提示按钮 - 动态折叠交互状态机  
**优先级**：P0  
**状态**：✅ 已完成  
**完成日期**：2026-04-16  

---

## 需求概述

### 设计原则
- 摒弃传统多按钮并列的求助模式
- 采用"单一主求助按钮"进行渐进式引导
- 降低认知负荷，防止学生直接查看答案

### 状态机定义（硬指标）

| 点击次数 | 当前按钮文案 | hint_level | Actual权重 | 是否标红 | 是否可见 |
|---------|-------------|-----------|-----------|---------|---------|
| 初始状态 | "给我点灵感" | -- | 1.0 | 否 | 是 |
| 第1次点击 | "还需要公式支持" | L1 | 0.8 | 否 | 是 |
| 第2次点击 | "带我走第一步" | L2 | 0.6 | 否 | 是 |
| 第3次点击 | "彻底没思路，看解析" | L3 | 0.4 | 是 | 是 |
| 第4次点击 | （隐藏） | L4 | 0.1 | 否 | 否 |

---

## 实现文件

### 1. 算法层
**文件**：`backend/algorithms/hint_button_state_machine.py` (250+行)

**核心类**：
- `HintButtonStateMachine` - 状态机主类
- `HintButtonState` - 状态枚举
- `ButtonConfig` - 按钮配置数据类

**关键方法**：
```python
# 用户点击按钮
click(user_id) -> Dict

# 重置状态机（学生答对时调用）
reset(user_id) -> Dict

# 获取完整状态
get_full_state(user_id) -> Dict

# 获取当前按钮配置
get_button_config(user_id) -> ButtonConfig
```

### 2. API层
**文件**：`backend/api/cognitive_diagnosis.py`

**新增端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/cognitive/hint-button/click` | 点击提示按钮 |
| POST | `/api/cognitive/hint-button/reset` | 重置状态机 |
| GET | `/api/cognitive/hint-button/state/{user_id}` | 获取按钮状态 |

### 3. Mock服务器
**文件**：`backend/mock_server_simple.py`

**Mock端点**：
- `POST /api/cognitive/hint-button/click`
- `POST /api/cognitive/hint-button/reset`
- `GET /api/cognitive/hint-button/state/{user_id}`

---

## API使用示例

### 点击提示按钮
```bash
curl -X POST http://localhost:8001/api/cognitive/hint-button/click \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

**响应示例**（第1次点击）：
```json
{
  "user_id": 1,
  "previous_state": "initial",
  "current_state": "level_1",
  "button_config": {
    "text": "还需要公式支持",
    "hint_level": 1,
    "actual_weight": 0.8,
    "is_highlighted": false,
    "is_visible": true
  },
  "click_count": 1,
  "hint_level": 1,
  "actual_weight": 0.8
}
```

### 获取按钮状态
```bash
curl http://localhost:8001/api/cognitive/hint-button/state/1
```

**响应示例**：
```json
{
  "user_id": 1,
  "current_state": "level_1",
  "click_count": 1,
  "button_config": {
    "text": "还需要公式支持",
    "hint_level": 1,
    "actual_weight": 0.8,
    "is_highlighted": false,
    "is_visible": true
  },
  "hint_level": 1,
  "actual_weight": 0.8,
  "is_visible": true,
  "is_highlighted": false
}
```

### 重置状态机（学生答对）
```bash
curl -X POST http://localhost:8001/api/cognitive/hint-button/reset \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

**响应示例**：
```json
{
  "user_id": 1,
  "state": "initial",
  "button_config": {
    "text": "给我点灵感",
    "hint_level": null,
    "actual_weight": 1.0,
    "is_highlighted": false,
    "is_visible": true
  },
  "click_count": 0,
  "hint_level": null,
  "actual_weight": 1.0,
  "message": "状态机已重置"
}
```

---

## 前端集成指南

### 1. 初始化按钮
```javascript
// 页面加载时获取按钮状态
const response = await fetch('/api/cognitive/hint-button/state/1');
const state = await response.json();

// 根据状态渲染按钮
renderButton({
  text: state.button_config.text,
  isVisible: state.is_visible,
  isHighlighted: state.is_highlighted
});
```

### 2. 点击按钮
```javascript
async function onHintButtonClick() {
  const response = await fetch('/api/cognitive/hint-button/click', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 1 })
  });
  
  const result = await response.json();
  
  // 更新按钮显示
  updateButton({
    text: result.button_config.text,
    isVisible: result.button_config.is_visible,
    isHighlighted: result.button_config.is_highlighted
  });
  
  // 请求Instructor下发对应等级的提示
  await requestInstructorHint(result.hint_level);
}
```

### 3. 提交正确答案后重置
```javascript
async function onSubmitAnswer(isCorrect) {
  if (isCorrect) {
    // 重置状态机
    await fetch('/api/cognitive/hint-button/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 1 })
    });
    
    // 恢复初始按钮
    updateButton({
      text: "给我点灵感",
      isVisible: true,
      isHighlighted: false
    });
  }
}
```

---

## 代码统计

| 模块 | 文件 | 代码行数 |
|------|------|---------|
| 算法层 | `algorithms/hint_button_state_machine.py` | 250+ |
| API层 | `api/cognitive_diagnosis.py` | 新增150+ |
| Mock层 | `mock_server_simple.py` | 新增80+ |
| **总计** | - | **480+行** |

---

## 验收标准

### 测试用例1：状态机流转
```
用户交互：连续点击4次按钮

预期结果：
- 第1次：文案变为"还需要公式支持"，hint_level=1，Actual=0.8
- 第2次：文案变为"带我走第一步"，hint_level=2，Actual=0.6
- 第3次：文案变为"彻底没思路，看解析"（标红），hint_level=3，Actual=0.4
- 第4次：按钮隐藏，hint_level=4，Actual=0.1
```

### 测试用例2：状态重置
```
用户交互：点击2次后提交正确答案

预期结果：
- 状态重置为initial
- 按钮文案恢复为"给我点灵感"
- hint_level=null，Actual=1.0
```

### 测试用例3：隐藏后点击
```
用户交互：点击4次（按钮隐藏）后继续点击

预期结果：
- 返回状态hidden
- 提示"按钮已隐藏"
- 不触发任何状态变化
```

---

## 下一步工作

1. **前端对接** - 集成渐进式提示按钮UI组件
2. **需求20** - 每日5题特训包开发
3. **需求29** - 记忆衰减Cron任务开发
