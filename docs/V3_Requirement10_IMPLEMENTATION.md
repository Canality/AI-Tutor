# 需求10实现文档：游戏技能树展示知识点依赖关系

**需求编号**：10  
**需求名称**：游戏技能树展示知识点依赖关系  
**优先级**：P0  
**状态**：✅ 已完成  
**完成日期**：2026-04-16  

---

## 需求概述

### 核心功能
1. **状态展示**：依据掌握度 P(L) 动态变色
   - 🟢 绿色：P(L) ≥ 0.8（已掌握）
   - 🟡 黄色：0.5 ≤ P(L) < 0.8（学习中）
   - 🔴 红色：P(L) < 0.5（薄弱点）
   - ⚪ 灰色：前置知识点未掌握时锁定

2. **核心交互**：点击红色/黄色节点，弹出"一键特训"悬浮按钮，唤起Advisor开启专属练习

3. **专题进度计算**：
   ```
   进度百分比 = (P(L) ≥ 0.8 的知识点数量) / (该专题总知识点数量)
   ```

---

## 实现文件

### 1. 算法层
**文件**：`backend/algorithms/skill_tree.py` (490+行)

**核心类**：
- `SkillTreeBuilder` - 技能树构建器主类
- `SkillTree` - 技能树数据类
- `KnowledgeNode` - 知识节点类
- `TopicProgress` - 专题进度类
- `NodeStatus` - 节点状态枚举

**关键方法**：
```python
# 构建用户技能树（带状态）
build_user_skill_tree(topic, user_mastery) -> SkillTree

# 计算节点状态（考虑前置依赖）
calculate_node_status(node, all_nodes) -> NodeStatus

# 计算专题进度
calculate_topic_progress(topic, user_mastery) -> TopicProgress

# 获取推荐训练节点（一键特训）
get_recommended_training(topic, user_mastery, limit) -> List[Dict]

# 获取已解锁节点
get_unlocked_nodes(topic, user_mastery) -> List[KnowledgeNode]
```

### 2. 默认技能树结构

#### 等差数列专题
```
Level 0: 数列基础概念 (根节点)
    ↓
Level 1: 等差数列定义
    ↓
Level 2: 等差数列通项公式 ──┬── 等差数列性质
    ↓                        │
Level 3: 等差数列求和公式 ◄───┘
    ↓
Level 4: 等差数列综合应用
```

#### 等比数列专题
```
Level 0: 数列基础概念 (依赖等差数列的根)
    ↓
Level 1: 等比数列定义
    ↓
Level 2: 等比数列通项公式
    ↓
Level 3: 等比数列求和公式
    ↓
Level 4: 等比数列综合应用
```

### 3. API层
**文件**：`backend/api/cognitive_diagnosis.py`

**新增端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/cognitive/skill-tree` | 获取用户技能树 |
| POST | `/api/cognitive/skill-tree/progress` | 获取专题进度 |
| POST | `/api/cognitive/skill-tree/recommendations` | 获取推荐训练 |
| GET | `/api/cognitive/skill-tree/topics` | 获取所有专题 |

### 4. Mock服务器
**文件**：`backend/mock_server_simple.py`

**Mock端点**：
- `POST /api/cognitive/skill-tree` - 模拟技能树查询
- `POST /api/cognitive/skill-tree/progress` - 模拟进度计算
- `POST /api/cognitive/skill-tree/recommendations` - 模拟推荐训练
- `GET /api/cognitive/skill-tree/topics` - 模拟专题列表

---

## API使用示例

### 获取技能树
```bash
curl -X POST http://localhost:8001/api/cognitive/skill-tree \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "topic": "等差数列"
  }'
```

**响应示例**：
```json
{
  "topic": "等差数列",
  "nodes": {
    "arith_001": {
      "node_id": "arith_001",
      "name": "数列基础概念",
      "topic": "等差数列",
      "p_known": 0.9,
      "status": "mastered",
      "prerequisites": [],
      "is_root": true,
      "position": {"x": 400, "y": 50, "level": 0}
    },
    "arith_002": {
      "node_id": "arith_002",
      "name": "等差数列定义",
      "topic": "等差数列",
      "p_known": 0.85,
      "status": "mastered",
      "prerequisites": ["arith_001"],
      "position": {"x": 200, "y": 150, "level": 1}
    },
    "arith_003": {
      "node_id": "arith_003",
      "name": "等差数列通项公式",
      "topic": "等差数列",
      "p_known": 0.6,
      "status": "learning",
      "prerequisites": ["arith_002"],
      "position": {"x": 200, "y": 250, "level": 2}
    },
    "arith_004": {
      "node_id": "arith_004",
      "name": "等差数列求和公式",
      "topic": "等差数列",
      "p_known": 0.3,
      "status": "locked",
      "prerequisites": ["arith_003"],
      "position": {"x": 200, "y": 350, "level": 3}
    }
  },
  "edges": [
    ["arith_001", "arith_002"],
    ["arith_002", "arith_003"],
    ["arith_003", "arith_004"]
  ],
  "total_nodes": 6
}
```

### 获取专题进度
```bash
curl -X POST http://localhost:8001/api/cognitive/skill-tree/progress \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "topic": "等差数列"
  }'
```

**响应示例**：
```json
{
  "topic": "等差数列",
  "total_nodes": 6,
  "mastered_nodes": 2,
  "learning_nodes": 1,
  "weak_nodes": 0,
  "locked_nodes": 3,
  "progress_percentage": 33.33,
  "progress_text": "33%"
}
```

### 获取推荐训练（一键特训）
```bash
curl -X POST http://localhost:8001/api/cognitive/skill-tree/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "topic": "等差数列",
    "limit": 3
  }'
```

**响应示例**：
```json
{
  "topic": "等差数列",
  "recommendations": [
    {
      "node_id": "arith_003",
      "name": "等差数列通项公式",
      "p_known": 0.6,
      "status": "learning",
      "topic": "等差数列"
    }
  ],
  "count": 1
}
```

---

## 算法测试结果

```
=== 测试1：等差数列技能树结构 ===
  专题: 等差数列
  节点数: 6
  边数: 6
  节点列表:
    - 数列基础概念 (ID: arith_001)
    - 等差数列定义 (ID: arith_002)
    - 等差数列通项公式 (ID: arith_003)
    - 等差数列求和公式 (ID: arith_004)
    - 等差数列性质 (ID: arith_005)
    - 等差数列综合应用 (ID: arith_006)

=== 测试2：构建用户技能树 ===
  节点状态:
    [G] 数列基础概念: P(L)=0.90 -> mastered
    [G] 等差数列定义: P(L)=0.85 -> mastered
    [Y] 等差数列通项公式: P(L)=0.60 -> learning
    [-] 等差数列求和公式: P(L)=0.30 -> locked
    [-] 等差数列性质: P(L)=0.40 -> locked
    [-] 等差数列综合应用: P(L)=0.00 -> locked

=== 测试3：专题进度计算 ===
  专题: 等差数列
  总节点: 6
  已掌握: 2
  学习中: 1
  薄弱点: 0
  锁定: 3
  进度: 33.3%

=== 测试4：推荐训练节点 ===
  推荐节点数: 1
    - 等差数列通项公式 (learning, P(L)=0.6)
```

---

## 前端集成指南

### 1. 渲染技能树
```javascript
// 获取技能树数据
const response = await fetch('/api/cognitive/skill-tree', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 1, topic: '等差数列' })
});
const tree = await response.json();

// 渲染节点
Object.values(tree.nodes).forEach(node => {
  const color = {
    'mastered': '#4CAF50',  // 绿色
    'learning': '#FFC107',  // 黄色
    'weak': '#f44336',      // 红色
    'locked': '#9E9E9E'     // 灰色
  }[node.status];
  
  renderNode(node.position.x, node.position.y, node.name, color);
});

// 渲染边（连接线）
tree.edges.forEach(([from, to]) => {
  const fromNode = tree.nodes[from];
  const toNode = tree.nodes[to];
  renderEdge(fromNode.position, toNode.position);
});
```

### 2. 节点点击交互
```javascript
function onNodeClick(node) {
  if (node.status === 'locked') {
    showToast('请先掌握前置知识点');
    return;
  }
  
  if (node.status === 'mastered') {
    showToast('该知识点已掌握');
    return;
  }
  
  // 显示"一键特训"按钮
  showTrainingButton(node, () => {
    startTraining(node.node_id);
  });
}
```

### 3. 显示专题进度
```javascript
// 获取进度
const response = await fetch('/api/cognitive/skill-tree/progress', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 1, topic: '等差数列' })
});
const progress = await response.json();

// 渲染进度条
renderProgressBar(progress.progress_percentage);
renderProgressText(`${progress.topic}已通关 ${progress.progress_text}`);
```

---

## 代码统计

| 模块 | 文件 | 代码行数 |
|------|------|---------|
| 算法层 | `algorithms/skill_tree.py` | 490+ |
| API层 | `api/cognitive_diagnosis.py` | 新增200+ |
| Mock层 | `mock_server_simple.py` | 新增150+ |
| **总计** | - | **840+行** |

---

## 下一步工作

1. **前端对接** - 集成技能树可视化组件
2. **需求16** - 渐进式提示按钮（单一按钮L0-L4）
3. **需求20** - 每日5题闯关任务

---

## 备注

- 所有掌握度阈值严格遵循PRD文档（0.8/0.5）
- 前置依赖检查确保学习路径的正确性
- 节点位置信息支持前端可视化渲染
- 推荐训练按掌握度升序排列，优先薄弱点
