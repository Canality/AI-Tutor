# 需求20 & 需求29 实现文档

---

## 需求20：每日5题特训包

**需求编号**：20  
**需求名称**：每日5题特训包  
**优先级**：P0  
**状态**：✅ 已完成  
**完成日期**：2026-04-16  

### 业务定义（硬指标）
将传统题海战术升级为"私人教练每日特训"。学生每日首次登录时，Advisor Agent自动下发5道题目的固定训练包。

### 动态混排配比规则（强制约束）

| 题型 | 占比 | 来源 | 选取逻辑 |
|-----|------|------|---------|
| 温故题 (复习) | 1-2题 | Redis Review Queue | 提取当前时间戳已到期的题目 |
| 攻坚题 (薄弱) | 2-3题 | Chroma向量库 | 查询P(L)<0.5的知识点，召回变式题 |
| 探索题 (拓展) | 1题 | 新题池 | 符合θ难度区间[θ-0.5, θ+0.5]的全新题目 |

### UI标签
- [温故] - 复习题
- [攻坚] - 薄弱点专项
- [探索] - 挑战新题

### 实现文件

#### 算法层
**文件**：`backend/algorithms/daily_training_pack.py` (280+行)

**核心类**：
- `DailyTrainingPackGenerator` - 特训包生成器
- `DailyTrainingPack` - 特训包数据类
- `DailyQuestion` - 题目数据类
- `QuestionType` - 题型枚举

**关键方法**：
```python
# 生成每日特训包
generate_pack(user_id, user_theta, user_mastery, review_queue, date) -> DailyTrainingPack

# 选取温故题
_select_review_questions(review_queue, count, used_ids) -> List[DailyQuestion]

# 选取攻坚题
_select_weak_questions(user_mastery, user_theta, count, used_ids) -> List[DailyQuestion]

# 选取探索题
_select_explore_questions(user_theta, count, used_ids) -> List[DailyQuestion]
```

### API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/cognitive/daily-pack` | 获取每日5题特训包 |

### API使用示例

```bash
curl -X POST http://localhost:8001/api/cognitive/daily-pack \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

**响应示例**：
```json
{
  "user_id": 1,
  "date": "2026-04-16",
  "total_questions": 5,
  "questions": [
    {
      "question_id": "q001",
      "question_type": "review",
      "type_label": "[温故]",
      "knowledge_point": "等差数列定义",
      "difficulty": 0.2,
      "reason": "距离上次做错已过去2天，测测肌肉记忆还在不在？"
    },
    {
      "question_id": "q003",
      "question_type": "weak",
      "type_label": "[攻坚]",
      "knowledge_point": "等差数列求和",
      "difficulty": 0.8,
      "reason": "你在【等差数列求和】方面还需要加强，这道题正好匹配你的水平。"
    }
  ],
  "type_distribution": {
    "review": 1,
    "weak": 2,
    "explore": 2
  }
}
```

---

## 需求29：记忆衰减定时任务 (Cron Job)

**需求编号**：29  
**需求名称**：记忆衰减定时任务  
**优先级**：P0  
**状态**：✅ 已完成  
**完成日期**：2026-04-16  

### 业务目的
模拟真实记忆半衰期，针对长时间未练习的知识点，执行掌握度P(L)的自然衰减。

### 定时任务规范（硬指标）

**执行频率**：每日凌晨 02:00 触发一次全局批处理任务

**目标数据表**：user_knowledge_mastery

**衰减公式**：
$$P(L_{t}) = P(L_{t-1}) \times e^{-\lambda \Delta t}$$

其中：
- $\lambda = \ln(2) / 7$（7天半衰期常数 ≈ 0.099）
- $\Delta t$ = 当前时间戳与 last_practiced_at 的天数差

### 执行逻辑
1. 扫描所有 last_practiced_at 小于 NOW() - INTERVAL 1 DAY 的记录
2. 按照衰减公式计算新的 P(L) 值
3. 执行批量更新（Batch Update）覆盖 p_known 字段
4. 缓存一致性：更新MySQL后，同步失效或更新 Redis `ai:tutor:mastery:{uid}`

### 衰减效果参考

| 天数 | 衰减因子 | P(L)=0.8衰减后 |
|-----|---------|---------------|
| 1天 | 0.9057 | 0.7246 |
| 7天 | 0.5 | 0.4 |
| 14天 | 0.25 | 0.2 |
| 30天 | 0.052 | 0.041 |

### 实现文件

#### 算法层
**文件**：`backend/algorithms/memory_decay_cron.py` (250+行)

**核心类**：
- `MemoryDecayCronJob` - 定时任务主类
- `DecayResult` - 衰减结果数据类

**关键方法**：
```python
# 计算衰减后的掌握度
calculate_decay(p_known, days_passed) -> float

# 判断是否需要衰减
should_decay(last_practiced_at, current_time) -> (bool, int)

# 执行定时任务（主入口）
execute_cron_job(current_time) -> Dict

# 同步Redis缓存
sync_redis_cache(user_id) -> bool

# 获取下次执行时间
get_next_execution_time(current_time) -> datetime
```

### API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/cognitive/cron/memory-decay` | 执行记忆衰减任务（测试用） |
| GET | `/api/cognitive/cron/memory-decay/next` | 获取下次执行时间 |

### API使用示例

#### 执行衰减任务（测试）
```bash
curl -X POST http://localhost:8001/api/cognitive/cron/memory-decay
```

**响应示例**：
```json
{
  "execution_time": "2026-04-16T02:00:00",
  "total_processed": 5,
  "total_decayed": 5,
  "results": [
    {
      "user_id": 1,
      "knowledge_point_id": 101,
      "p_known_before": 0.9,
      "p_known_after": 0.7246,
      "days_passed": 1,
      "decay_factor": 0.9057
    },
    {
      "user_id": 1,
      "knowledge_point_id": 103,
      "p_known_before": 0.7,
      "p_known_after": 0.35,
      "days_passed": 7,
      "decay_factor": 0.5
    }
  ]
}
```

#### 获取下次执行时间
```bash
curl http://localhost:8001/api/cognitive/cron/memory-decay/next
```

**响应示例**：
```json
{
  "next_execution": "2026-04-17T02:00:00",
  "hour": 2,
  "minute": 0
}
```

---

## 代码统计

| 需求 | 模块 | 文件 | 代码行数 |
|-----|------|------|---------|
| 需求20 | 算法层 | `daily_training_pack.py` | 280+ |
| 需求20 | API层 | `cognitive_diagnosis.py` | 新增80+ |
| 需求20 | Mock层 | `mock_server_simple.py` | 新增50+ |
| 需求29 | 算法层 | `memory_decay_cron.py` | 250+ |
| 需求29 | API层 | `cognitive_diagnosis.py` | 新增60+ |
| 需求29 | Mock层 | `mock_server_simple.py` | 新增30+ |
| **总计** | - | - | **750+行** |

---

## 验收标准

### 需求20验收标准

**测试用例1：题型配比**
```
用户交互：获取每日特训包

预期结果：
- 总题数 = 5
- 温故题 1-2题
- 攻坚题 2-3题
- 探索题 1题
- 每道题都有[温故]/[攻坚]/[探索]标签
```

**测试用例2：攻坚题选取**
```
用户交互：用户有P(L)<0.5的知识点

预期结果：
- 攻坚题优先选取薄弱知识点的变式题
- 推荐理由中包含薄弱知识点名称
```

### 需求29验收标准

**测试用例1：7天半衰期**
```
输入：P(L)=0.8, 7天未练习

预期结果：
- 衰减后P(L) ≈ 0.4
- 衰减因子 = 0.5
```

**测试用例2：Cron执行**
```
用户交互：调用Cron执行API

预期结果：
- 只处理last_practiced_at > 1天的记录
- 返回处理记录数和衰减详情
- 包含衰减前/后的P(L)值
```

---

## 下一步工作

1. **前端对接** - 集成每日特训包UI和记忆衰减展示
2. **生产环境部署** - 配置Cron定时任务调度器
3. **其他需求开发** - 根据优先级继续开发
