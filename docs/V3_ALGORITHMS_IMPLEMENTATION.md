# AI Tutor V3 认知诊断算法实现文档

## 完成情况

### 已实现的算法模块

| 算法 | 文件 | PRD参数 | 状态 |
|------|------|---------|------|
| **BKT** | `algorithms/bkt.py` | P(T)=0.3, P(G)=0.2, P(S)=0.1, P(L0)=0.5 | ✅ 完成 |
| **IRT** | `algorithms/irt_simple.py` | theta∈[-3,+3], b∈[-3,+3], a=1.0 | ✅ 完成 |
| **K-IRT** | `algorithms/irt_simple.py` | n>10时α=0.8, n≤10时α=0.3 | ✅ 完成 |
| **自适应K因子** | `algorithms/adaptive_k.py` | β=0.1, γ=0.5, K_initial=0.3 | ✅ 完成 |
| **记忆衰减** | `algorithms/memory_decay.py` | 半衰期7天, λ=ln(2)/7 | ✅ 完成 |
| **Actual Score** | `algorithms/actual_score.py` | L0-L4权重1.0/0.8/0.6/0.4/0.1 | ✅ 完成 |

### 创建的文件

```
backend/
├── algorithms/
│   ├── __init__.py              # 模块导出
│   ├── bkt.py                   # BKT算法 (200+行)
│   ├── irt.py                   # IRT完整版 (250+行，依赖numpy)
│   ├── irt_simple.py            # IRT简化版 (100+行，无依赖)
│   ├── adaptive_k.py            # 自适应K因子 (180+行)
│   ├── memory_decay.py          # 记忆衰减 (200+行)
│   ├── actual_score.py          # Actual Score (250+行)
│   ├── requirements.txt         # 依赖说明
│   └── test_integration.py      # 集成测试
│
├── services/
│   └── cognitive_diagnosis_service.py  # 认知诊断服务 (300+行)
│
└── api/
    └── cognitive_diagnosis.py   # REST API接口 (250+行)
```

**总计：1500+行代码**

---

## API端点

### 1. 更新掌握度 (BKT)
```http
POST /api/cognitive/mastery/update
```
**请求体：**
```json
{
  "user_id": 1,
  "knowledge_point_id": 101,
  "is_correct": true
}
```
**响应：**
```json
{
  "user_id": 1,
  "knowledge_point_id": 101,
  "p_known": 0.8727,
  "mastery_level": "learning"
}
```

### 2. 获取能力值 (K-IRT)
```http
GET /api/cognitive/theta/{user_id}
```
**响应：**
```json
{
  "user_id": 1,
  "theta": 0.5234,
  "theta_irt": 0.6000,
  "theta_bkt": 0.4000,
  "alpha": 0.8,
  "theta_se": 0.3015,
  "ci_lower": -0.0675,
  "ci_upper": 1.1143
}
```

### 3. 计算Actual Score
```http
POST /api/cognitive/actual-score/calculate
```
**请求体：**
```json
{
  "is_correct": true,
  "hint_level": 2,
  "time_spent": 60,
  "expected_time": 60,
  "skip_reason": null
}
```
**响应：**
```json
{
  "actual_score": 0.7500,
  "hint_level_name": "公式提示",
  "components": {
    "correctness": true,
    "hint_weight": 0.6,
    "time_ratio": 1.0,
    "skip_reason": null
  }
}
```

### 4. 获取推荐难度范围
```http
GET /api/cognitive/difficulty-range/{user_id}
```
**响应：**
```json
{
  "theta": 0.5,
  "min_difficulty": 0.0,
  "max_difficulty": 1.0,
  "recommended_range": "[0.0, 1.0]"
}
```

### 5. 获取综合诊断报告
```http
GET /api/cognitive/report/{user_id}
```
**响应：**
```json
{
  "user_id": 1,
  "ability": {...},
  "mastery_distribution": {
    "mastered": 5,
    "learning": 3,
    "weak": 2,
    "total": 10
  },
  "recommended_difficulty": {...},
  "generated_at": "2026-04-15T21:50:00"
}
```

### 6. 应用记忆衰减
```http
POST /api/cognitive/memory-decay/apply
```
**请求体：**
```json
{
  "user_id": 1
}
```

### 7. 健康检查
```http
GET /api/cognitive/health
```

---

## 算法测试结果

```
BKT: 连续答对3次，掌握度 0.5 -> 0.9965 ✓
IRT: theta=-3时P=0.047, theta=+3时P=0.953 ✓
自适应K: 方向一致时K增大(0.32)，震荡时K减小(0.27) ✓
记忆衰减: 7天后掌握度减半(0.8 -> 0.4) ✓
Actual Score: L0=0.85, L4=0.625 ✓
```

---

## 使用示例

### Python调用
```python
from algorithms import BKTModel, IRTModel, ActualScoreCalculator

# BKT更新掌握度
bkt = BKTModel()
p_new = bkt.update(p_old=0.5, is_correct=True)

# IRT计算答对概率
irt = IRTModel()
prob = irt.probability_correct(theta=0.5, question)

# 计算Actual Score
calc = ActualScoreCalculator()
score = calc.calculate(record)
```

### HTTP调用
```python
import requests

# 更新掌握度
response = requests.post(
    "http://localhost:8000/api/cognitive/mastery/update",
    json={"user_id": 1, "knowledge_point_id": 101, "is_correct": True}
)
print(response.json())
```

---

## 下一步工作

1. **启动后端服务** - 激活虚拟环境，运行 `python main.py`
2. **测试API** - 使用Swagger UI或Postman测试接口
3. **前端集成** - 前端调用这些API显示掌握度和能力值
4. **性能优化** - 添加缓存、批量处理等优化

---

## 注意事项

- IRT有两个版本：`irt.py`（完整版，依赖numpy）和 `irt_simple.py`（简化版，无依赖）
- 当前使用简化版IRT，如需完整功能请安装numpy和scipy
- 所有算法参数严格遵循PRD文档，为硬指标
