# AI Tutor V3 功能结构文档(PRD版)
文档级别: PRD(产品需求文档)
版本: V3.0-FINAL
日期: 2026-04-14
状态: 设计中 | 研发就绪

---

## 一、核心计算引擎
### 1.1 用户画像(认知诊断引擎)
#### 1.1.1 数据采集层
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| actual_score | FLOAT | 软标签得分 (0.0-1.0) |
| hint_count | INT | 使用提示次数 |
| time_spent | INT | 答题耗时(秒) |
| skip_reason | ENUM | 跳过原因:too_easy / too_hard / other |

#### 1.1.2 BKT 知识追踪(贝叶斯知识追踪)
核心公式:
$$P\left(L_{n+1}\right)=P\left(L_n | obs\right)+\left[1-P\left(L_n | obs\right)\right] \times P(T)$$

**参数说明(硬指标 - Baseline):**
| 参数 | 符号 | 默认值 | 说明 |
| --- | --- | --- | --- |
| 学习概率 | $P(T)$ | 0.3 | 未掌握时通过练习掌握的概率 |
| 猜测概率 | $P(G)$ | 0.2 | 未掌握时猜对的概率 |
| 失误概率 | $P(S)$ | 0.1 | 掌握后答错的概率 |
| 初始掌握度 | $P(L_0)$ | 0.5 | 初始先验概率 |

**数据表扩展(user_knowledge_mastery 表):**
```sql
ALTER TABLE user_knowledge_mastery
ADD COLUMN p_learn FLOAT DEFAULT 0.3,
ADD COLUMN p_guess FLOAT DEFAULT 0.2,
ADD COLUMN p_slip FLOAT DEFAULT 0.1,
ADD COLUMN p_known FLOAT DEFAULT 0.5;
```

#### 1.1.3 IRT 能力评估(项目反应理论)
核心公式:
$$P(\text{correct}) = \frac{1}{1 + e^{-a(\theta - b)}}$$

**参数说明(硬指标 - Baseline):**
| 参数 | 说明 |
| --- | --- |
| 能力值 | 学生能力估计值(-3 ~ +3) |
| 题目难度 | 题目难度参数(-3 ~ +3) |
| 区分度 | 题目区分度(默认 1.0) |

**K-IRT 联合估算(硬指标 - Baseline):**
$$\theta_{final} = \alpha \times \theta_{IRT} + (1 - \alpha) \times \theta_{BKT}$$

| 条件 | $\alpha$ 值 | 策略 |
| --- | --- | --- |
| 答题记录充足 (n > 10) | 0.8 | 主要依赖 IRT |
| 答题记录稀疏 (n ≤ 10) | 0.3 | 主要依赖 BKT 先验 |

**自适应 K 因子优化(硬指标 - Baseline):**
$$K_{adaptive} = K_{initial} + \beta \times \left( \frac{|\theta_{new} - \theta_{old}|}{1 + \gamma} \right)$$

| 参数 | 符号 | 说明 |
| --- | --- | --- |
| 初始学习步长 | $K_{initial}$ | 初始 K 值 |
| 调整幅度系数 | $\beta$ | 控制调整幅度 |
| 非线性压缩因子 | $\gamma$ | 压缩大幅波动 |

**数据表扩展(user_profiles 表):**
```sql
ALTER TABLE user_profiles
ADD COLUMN theta FLOAT NULL,
ADD COLUMN theta_se FLOAT NULL,
ADD COLUMN theta_ci_lower FLOAT NULL,
ADD COLUMN theta_ci_upper FLOAT NULL;
```

#### 1.1.4 错误分析与软标签(Soft Labeling)
**Actual Score 计算公式(硬指标 - Baseline):**
$$\text{Actual Score} = w_{correct} \times S_{correct} + w_{hint} \times S_{hint} + w_{time} \times S_{time} + w_{skip} \times S_{skip}$$

**权重配置(硬指标 - Baseline):**
| 权重 | 说明 |
| --- | --- |
| $w_{correct}$ | 正确性权重(最高) |
| $w_{hint}$ | 提示使用权重 |
| $w_{time}$ | 时间效率权重 |
| $w_{skip}$ | 跳过行为权重 |

**子分数计算规则:**
| 指标 | 满分条件 | 零分条件 |
| --- | --- | --- |
| $S_{correct}$ | 完全正确 | 完全错误或部分正确 |
| $S_{hint}$ | 未使用提示 | 使用全部提示 |
| $S_{time}$ | 时间 ≤ 预期时间 | 时间 > 预期时间 × 2 |
| $S_{skip}$ | 未跳过 | 跳过题目 |

#### 1.1.5 难度适应性计算(硬指标 - Baseline)
基础推荐难度区间:
$$S_{next} \in [\theta - 0.5, \theta + 0.5]$$

**动态调整规则(硬指标 - Baseline):**
| 条件 | 调整方式 |
| --- | --- |
| 连续正确(连续 3 题) | $S_{next}$ 上限 += 0.3 |
| 连续错误(连续 2 题) | $S_{next}$ 下限 -= 0.3 |

**推荐策略优先级:**
1. 优先推荐复习队列中的错题(若到期)
2. 其次推荐薄弱知识点相关题目
3. 最后按难度区间推荐新题

---

## 二、Instructor(讲师Agent)
**工程规范强制要求:** 所有数学推导公式必须严格采用标准LaTeX语法输出,确保前端渲染无误。

### 2.1 模型对话
#### 2.1.1 引导式教学
| 用户表达 | 检测关键词 | 系统画像更新 | Instructor响应策略 |
| --- | --- | --- | --- |
| 困难感知 | "好难"、"太难了" | 标记该知识点难度感知+1 | 分解步骤,增加中间推导 |
| 信心充足 | "能克服"、"简单" | 标记学习风格为"进取型" | 减少提示,鼓励自主探索 |
| 步骤困惑 | "看不懂"、"跳太快" | 标记需要详细解释 | 展开被省略的中间步骤 |

### 2.2 分等级提示系统
#### 2.2.1 提示等级定义
| 等级 | 触发条件 | Instructor行为 | Actual权重 |
| --- | --- | --- | --- |
| L0-自主(待商榷) | 学生直接提交答案 | 仅批改,不干预 | 1.0 |
| L1-方向(待商榷) | 学生点击"有点思路但卡住了" | 给出解题方向提示 | 0.8 |
| L2-公式(待商榷) | 学生点击"需要公式提醒" | 给出相关公式定理 | 0.6 |
| L3-步骤(待商榷) | 学生点击"教教我" | 给出关键推导步骤 | 0.4 |
| L4-答案(待商榷) | 学生点击"看答案" | 给出完整解答 | 0.1 |

### 2.3 推荐题处理
#### 2.3.1 解题思路提交与批改
流程:
1. 学生完成推荐题后,系统提示"请上传你的解题思路"
2. 学生上传后,Instructor进行分步批改
3. 标记错误步骤,给出针对性反馈
4. 更新Actual Score(基于错误步骤比例加权)

### 2.4 跳过处理机制
| 跳过类型 | 用户心理 | 算法处理 | Advisor介入话术 |
| --- | --- | --- | --- |
| 太简单 | 系统看低我了,浪费时间 | Actual=1.0, θ+=0.1, BKT 提升 | "看来这些基础难不倒你!我们直接跳过这一阶,挑战更深的内容。" |
| 太难了 | 系统高估我了,感到挫败 | Actual=0.0, θ-=0.05, U增加 | "这道题涉及的放缩法确实超前,别灰心,我先为你降低难度。" |

---

## 三、Advisor(顾问Agent)
### 3.1 触发与参数预处理
#### 3.1.1 触发场景
| 触发类型 | 触发条件 | 预处理动作 |
| --- | --- | --- |
| 主动请求 | 学生点击"推荐题目" | 读取完整画像,执行完整推荐流程 |
| 被动触发 | 当前题目完成后自动触发 | 快速读取Redis缓存,执行轻量推荐 |
| 定时触发 | 每日学习提醒 | 基于历史数据生成日计划 |

#### 3.1.2 参数提取
```python
# 伪代码
user_theta = redis.hget(f"ai:tutor:mastery:{uid}", "global_theta")
weak_kps = get_lowest_mastery_kps(uid, top_n=3) # 掌握度最低的3个知识点
recent_context = get_recent_chat_context(uid, last_n=5) # 最近5轮对话
```

### 3.2 Advisor Agent 指令集
Advisor通过向Instructor下发控制指令,调控教学策略和讲解深度。

| 指令编码 | 指令名称 | 触发条件 | 控制参数 | Instructor行为约束 |
| --- | --- | --- | --- | --- |
| MODE_SCAFFOLD | 脚手架模式 | 学生掌握度 < 0.4 或 连续2题错误 | detailed, true, hint_level: step_by_step: true allow_skip: | 必须分步讲解,每步后确认理解,允许随时请求提示 |
| MODE_CHALLENGE | 挑战模式 | 学生掌握度 > 0.8 且 近期正确率高 | minimal, false, false hint_level: step_by_step: allow_skip: | 仅给出方向性提示,要求学生自主推导,不展开中间步骤 |
| MODE_ENCOURAGE | 鼓励模式 | 学生连续3题错误或 主动表达挫败感 | adaptive, true, true hint_level: step_by_step: encouragement: | 先给予情感支持,再逐步引导,强调"错误是学习机会" |

**指令下发格式:**
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

### 3.3 候选池构建(基于向量数据库)
#### 3.3.1 RAG初筛
```python
输入:weak_kps = ["等比数列", "递推公式"]
输出:candidate_pool = vector_search(weak_kps, top_k=50)
```

#### 3.3.2 元数据过滤
```python
过滤条件:
- |S - θ| ≤ 1.0 (难度匹配)
- question_id ∉ SeenSet (去重)
- knowledge_points ∩ weak_kps ≠ ∅ (知识点相关)
```

#### 3.3.3 相似度加权
```python
context_similarity = cosine_similarity(recent_context, question_content)
final_score = 0.6 × kp_relevance + 0.3 × difficulty_match + 0.1 × context_similarity
```

### 3.4 Redis过滤与重排序
#### 3.4.1 去重过滤器
```python
# Redis Set结构
seen_key = f"ai:tutor:seen-q:{uid}"
for qid in candidate_pool:
    if redis.sismember(seen_key, qid):
        candidate_pool.remove(qid) # 已做题目剔除
```

#### 3.4.2 冷热调度
```python
# Redis ZSet结构
review_key = f"ai:tutor:review-q:{uid}"
now = time.time()
due_reviews = redis.zrangebyscore(review_key, 0, now) # 获取已到期的复习题

if due_reviews:
    # 优先推送复习题
    final_candidates = due_reviews[:3] + new_candidates[:2]
else:
    # 全部推送新题
    final_candidates = new_candidates[:5]
```

#### 3.4.3 策略权重分配
| 策略 | 权重 | 选取逻辑 |
| --- | --- | --- |
| 新题探索(Exploration) | 70% | 从未做过的变式题,拓展知识边界 |
| 旧题复盘(Review) | 30% | Redis队列中高频做错的题目,巩固薄弱点 |

### 3.5 推荐指令生成(LLM适配层)
#### 3.5.1 理由合成
```python
输入:选中题目Q,用户画像P
输出:自然语言推荐理由
模板:
"根据你的学习记录,你在【{weak_kp}】方面还需要加强。
这道题难度为{difficulty},正好匹配你当前的能力水平。
建议用时{estimated_time}分钟,完成后我会为你详细讲解。"
```

#### 3.5.2 难度适配与语气调整
| 推荐类型 | Agent语气 | 示例话术 |
| --- | --- | --- |
| 降级推荐(太难了→简单) | 鼓励型 | "这道题确实有些挑战,我们先从基础练起,打好基础再回来攻克它!" |
| 同级推荐 | 中性 | "这道题的考点和你刚做的类似,试试看能不能举一反三?" |
| 升级推荐(太简单→挑战) | 激励型 | "上一题你完成得很棒!这道进阶题能帮你更上一层楼,敢不敢挑战一下?" |

### 3.6 反馈闭环(Redis写入)
```python
# 更新Seen Set
redis.sadd(f"ai:tutor:seen-q:{uid}", question_id)

# 更新Review Queue(如果做错)
if not is_correct:
    next_review = calculate_next_review_time(error_count)
    redis.zadd(f"ai:tutor:review-q:{uid}", {question_id: next_review})

# 更新Mastery Hash
redis.hset(f"ai:tutor:mastery:{uid}", kp_id, new_mastery_score)
```

---

## 四、Redis 核心数据结构设计(Key-Schema,待商榷)
### 4.1 已做题目去重池(Seen Pool,待商榷)
| 属性 | 值(待商榷) |
| --- | --- |
| 数据结构 | Set |
| Key | ai:tutor:seen-q:{uid} |
| 内容 | [question_id_1, question_id_2, ...] |
| TTL | 无(持久化至 MySQL 后重建) |
| 说明 | 每次推题前,利用 SISMEMBER 快速排除已做题目 |

### 4.2 错题复习优先队列(Review Queue,待商榷)
| 属性 | 值(待商榷) |
| --- | --- |
| 数据结构 | ZSet (Sorted Set) |
| Key | ai:tutor:review-q:{uid} |
| Score | next_review_timestamp (下次复习的时间戳) |
| Member | question_id |
| TTL | 30 天 |
| 说明 | 每次推题引擎工作时,先执行 ZRANGEBYSCORE 检查是否有到期需要复习的错题 |

**复习间隔计算(Spaced Repetition,待商榷):**
第 n 次错误后的下次复习时间: $T_n = T_{n-1} * 2$ (指数退避)，具体间隔天数待商榷

### 4.3 实时掌握度(Real-time Mastery,待商榷)
| 属性 | 值(待商榷) |
| --- | --- |
| 数据结构 | Hash |
| Key | ai:tutor:mastery:{uid} |
| Field | knowledge_point_id |
| Value | score (0-100 整数) |
| TTL | 7 天 |
| 说明 | 推荐引擎直接从 Redis Hash 中 O(1) 速度读取分数,决定下一题的难度 |

### 4.4 Key-Schema 命名规范总结(待商榷)
| 数据类型 | Key 模式 | 数据结构 | 主要用途 | 持久化策略 |
| --- | --- | --- | --- | --- |
| 已做题目去重池 | ai:tutor:seen-q:{uid} | Set | 防止重复推题 | Session 后异步写入 MySQL |
| 错题复习队列 | ai:tutor:review-q:{uid} | ZSet | 优先级复习调度 | 实时同步至 MySQL |
| 实时掌握度 | ai:tutor:mastery:{uid} | Hash | 快速读取认知状态 | 每 5 分钟批量同步 |
| 当前 Session 状态 | ai:tutor:session:{sid} | Hash | 临时状态存储 | Session 结束后删除 |

---

## 五、画像逻辑存储层(基于现有 MySQL 扩展)
### 5.1 现有表复用(无需修改)
| 表名 | 说明 |
| --- | --- |
| users | 用户基础信息 |
| questions | 题目数据 |
| chat_sessions | 会话管理 |
| chat_messages | 消息记录 |
| solution_steps | 解题步骤 |
| knowledge_points | 知识点表 |
| question_knowledge_points | 题目-知识点关联 |

### 5.2 现有表扩展(ALTER TABLE)
#### 5.2.1 learning_records 表扩展
1. 现有字段:id, user_id, question_id, source_type, custom_question_data, is_correct, user_answer, ai_feedback, recommendation_session_id, recommendation_algorithm_version, created_at
2. V3 新增字段:
```sql
-- 使用提示次数
ALTER TABLE learning_records ADD COLUMN hint_count INT DEFAULT 0;
-- 答题耗时(秒)
ALTER TABLE learning_records ADD COLUMN time_spent INT NULL;
-- 跳过原因(too_easy / too_hard / other)
ALTER TABLE learning_records ADD COLUMN skip_reason VARCHAR(20) NULL;
-- IRT 能力值(答题前)
ALTER TABLE learning_records ADD COLUMN theta_before FLOAT NULL;
-- IRT 能力值(答题后)
ALTER TABLE learning_records ADD COLUMN theta_after FLOAT NULL;
-- 各知识点掌握度更新(JSON 格式)
ALTER TABLE learning_records ADD COLUMN mastery_updates JSON NULL;
```

#### 5.2.2 user_profiles 表扩展
1. 现有字段:id, user_id, knowledge_mastery, weak_points, total_questions, correct_count, updated_at
2. V3 新增字段:
```sql
-- 标准误差
ALTER TABLE user_profiles ADD COLUMN theta_se FLOAT NULL;
-- 95% 置信区间下限
ALTER TABLE user_profiles ADD COLUMN theta_ci_lower FLOAT NULL;
-- 95% 置信区间上限
ALTER TABLE user_profiles ADD COLUMN theta_ci_upper FLOAT NULL;
-- 平均掌握度
ALTER TABLE user_profiles ADD COLUMN avg_mastery FLOAT NULL;
-- 薄弱知识点数量
ALTER TABLE user_profiles ADD COLUMN weak_kp_count INT DEFAULT 0;
-- 学习风格
ALTER TABLE user_profiles ADD COLUMN learning_style VARCHAR(20) NULL;
-- 掌握度计算策略
ALTER TABLE user_profiles ADD COLUMN mastery_strategy VARCHAR(20) DEFAULT 'simple';
```

#### 5.2.3 user_knowledge_mastery 表扩展
1. 现有字段:id, user_id, knowledge_point_id, mastery_level, practice_count, correct_count, last_practiced_at, updated_at
2. V3 新增字段(BKT 参数):
```sql
-- BKT 猜测概率 P(G)
ALTER TABLE user_knowledge_mastery ADD COLUMN p_guess FLOAT DEFAULT 0.2;
-- BKT 失误概率 P(S)
ALTER TABLE user_knowledge_mastery ADD COLUMN p_slip FLOAT DEFAULT 0.1;
-- BKT 当前掌握概率 P(L)
ALTER TABLE user_knowledge_mastery ADD COLUMN p_known FLOAT DEFAULT 0.5;
-- 连续正确次数
ALTER TABLE user_knowledge_mastery ADD COLUMN consecutive_correct INT DEFAULT 0;
-- 连续错误次数
ALTER TABLE user_knowledge_mastery ADD COLUMN consecutive_wrong INT DEFAULT 0;
```

### 5.3 新增表(V3 新建)
#### 5.3.1 能力历史表(user_ability_history)
```sql
CREATE TABLE user_ability_history (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
theta FLOAT NOT NULL,
theta_se FLOAT NULL,
theta_ci_lower FLOAT NULL,
theta_ci_upper FLOAT NULL,
avg_mastery FLOAT NULL,
weak_kp_count INT DEFAULT 0,
total_questions INT DEFAULT 0,
correct_count INT DEFAULT 0,
recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
INDEX idx_user_time (user_id, recorded_at)
);
```

#### 5.3.2 错题本表(mistake_book)
```sql
CREATE TABLE mistake_book (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
question_id INT NOT NULL,
error_count INT DEFAULT 1,
first_error_at DATETIME DEFAULT CURRENT_TIMESTAMP,
last_error_at DATETIME DEFAULT CURRENT_TIMESTAMP,
mastered BOOLEAN DEFAULT FALSE,
mastered_at DATETIME NULL,
review_count INT DEFAULT 0,
last_review_at DATETIME NULL,
next_review_at DATETIME NULL,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
UNIQUE KEY uk_user_question (user_id, question_id),
INDEX idx_user_mastered (user_id, mastered),
INDEX idx_next_review (user_id, next_review_at)
);
```

#### 5.3.3 收藏夹表(favorites)
```sql
CREATE TABLE favorites (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
question_id INT NOT NULL,
folder_name VARCHAR(50) DEFAULT '默认收藏夹',
note TEXT NULL,
tags JSON NULL,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
UNIQUE KEY uk_user_question (user_id, question_id),
INDEX idx_user_folder (user_id, folder_name)
);
```

#### 5.3.4 交互日志表(user_interaction_logs,可选)
```sql
CREATE TABLE user_interaction_logs (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
session_id VARCHAR(100) NULL,
interaction_type VARCHAR(50) NOT NULL,
question_id INT NULL,
knowledge_points JSON NULL,
difficulty INT NULL,
content TEXT NULL,
metadata JSON NULL,
sentiment_tag VARCHAR(20) NULL,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
INDEX idx_user_time (user_id, created_at),
INDEX idx_session (session_id)
);
```

### 5.4 数据流与同步策略
#### 5.4.1 高频读写路径(Redis)
```
推题请求 → 读取 Redis Seen Set/Review Queue/Mastery Hash → 返回候选题目
毫秒级响应(目标待商榷)
```

#### 5.4.2 异步持久化路径(MySQL)
```
Session 结束 → 批量写入 learning_records → 更新 user_knowledge_mastery 写入 user_interaction_logs → 更新 user_ability_history
秒级延迟可接受
```

#### 5.4.3 数据一致性保障(待商榷)
| 场景 | 策略 | 说明 |
| --- | --- | --- |
| Redis 故障 | 降级读取 MySQL | 推题延迟增加,但服务可用 |
| 写入冲突 | 乐观锁+重试 | 用户画像更新使用版本号控制 |
| 数据丢失 | 消息队列缓冲 | 关键操作先入 MQ,再写入 Redis/MySQL |
| 冷启动 | 从 MySQL 重建 Redis | 用户首次访问时异步加载历史数据 |

---

## 六、功能展示与应用层
### 6.1 学生端功能
#### 6.1.1 六维雷达图
展示维度:待商榷
数据来源:user_knowledge_mastery 表聚合计算

#### 6.1.2 知识树变色(待设计)
待商榷:颜色定义、掌握度范围划分、前置知识点解锁逻辑

| 颜色 | 含义 | 掌握度范围 |
| --- | --- | --- |
| 绿色 | 已掌握 | P(L) ≥ 0.8 |
| 黄色 | 学习中 | 0.4 ≤ P(L) < 0.8 |
| 红色 | 薄弱点 | P(L) < 0.4 |
| 灰色 | 未解锁 | 前置知识点未掌握 |

### 6.2 Agent端功能
#### 6.2.1 个性化引导语(待设计)
待商榷:引导语触发条件、内容模板、显示时机
触发条件:针对"计算易错型"学生(Trait_Tags包含'calculation_error_prone')
Agent行为:在输出数学推导步骤前,自动插入提醒:
`⚠️ 注意:这一步涉及计算,请仔细核对符号和数值。`

#### 6.2.2 自适应推题流(待设计)
待商榷:薄弱点题目注入逻辑、候选池排序算法
触发条件:RAG检索时,自动加入Mastery_Score < 0.4的相关题型
实现逻辑:
```sql
-- 在候选池构建时注入薄弱点题目
SELECT * FROM questions
WHERE knowledge_point IN (
SELECT kp_id FROM user_knowledge_mastery
WHERE user_id = ? AND p_known < 0.4
)
ORDER BY random() LIMIT 3
```

#### 6.2.3 报告导出(待设计)
待商榷:报告类型、内容模板、导出格式、生成频率
报告类型:
- 周报:本周答题统计、能力值变化、薄弱点分析
- 月报:月度学习趋势、知识点掌握度变化、学习建议
- 专项报告:针对特定知识点的深度分析
导出格式:PDF / Markdown

---

## 七、工程规范与约束
### 7.1 LaTeX公式输出规范(强制)
所有数学推导公式必须严格采用标准LaTeX语法输出,确保前端渲染无误。

#### 7.1.1 行内公式
使用单美元符号包裹:
```
等差数列求和公式: $S_n = \frac{n(a_1 + a_n)}{2}$
```

#### 7.1.2 独立公式
使用双美元符号或equation环境:
```
$$S_n = na_1 + \frac{n(n-1)}{2}d$$
```

#### 7.1.3 多行对齐
使用align环境:
```
$$\begin{align}
a_n &= a_1 + (n-1)d \\
&= a_m + (n-m)d
\end{align}$$
```

#### 7.1.4 常见符号对照
| 数学概念 | LaTeX语法 | 渲染效果 |
| --- | --- | --- |
| 上标 | x^2 | $x^2$ |
| 下标 | a_n | $a_n$ |
| 分数 | \frac{a}{b} | $\frac{a}{b}$ |
| 根号 | \sqrt{x} | $\sqrt{x}$ |
| 求和 | \sum_{i=1}^{n} | $\sum_{i=1}^{n}$ |
| 希腊字母 | \theta , \lambda | $\theta , \lambda$ |

### 7.2 API 响应时间约束(待商榷)
| 接口类型 | 目标响应时间 | 最大容忍时间 | 说明 |
| --- | --- | --- | --- |
| 推题接口 | 待商榷 | 待商榷 | Redis 缓存命中 |
| 能力评估查询 | 待商榷 | 待商榷 | 基于 MySQL 索引优化 |
| 流式教学响应 | 待商榷 | 待商榷 | Instructor 首字节返回 |
| 历史记录查询 | 待商榷 | 待商榷 | 分页查询优化 |

### 7.3 数据安全与隐私
- 用户密码:bcrypt加密存储, cost factor ≥12
- 敏感操作:JWT Token验证,有效期15分钟
- 数据传输:HTTPS强制加密
- 日志脱敏:用户ID哈希化,敏感内容过滤

---

## 八、附录
### 8.1 参考文献
1. Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural knowledge. User Modeling and User-Adapted Interaction, 4(4), 253-278.
2. Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. In Proceedings of ACL, 1848-1858.
3. Lord, F. M. (1980). Applications of item response theory to practical testing problems. Lawrence Erlbaum Associates.
4. Piech, C., et al. (2015). Deep knowledge tracing. In Proceedings of NIPS, 505-513.

### 8.2 术语表
| 术语 | 英文 | 说明 |
| --- | --- | --- |
| 能力值 | Theta (θ) | IRT模型中的学生能力参数 |
| 掌握概率 | P(L) | BKT模型中学生掌握某知识点的概率 |
| 学习概率 | P(T) | BKT模型中从未掌握到掌握的状态转移概率 |
| 猜测概率 | P(G) | BKT模型中未掌握时猜对的概率 |
| 失误概率 | P(S) | BKT模型中掌握时做错的概率 |
| 软标签 | Soft Label | 综合考虑多因素的评分机制 |
| 脚手架 | Scaffold | 逐步引导的教学策略 |

### 8.3 变更日志
| 版本 | 日期 | 变更内容 | 作者 |
| --- | --- | --- | --- |
| v3.0-FINAL | 2026-04-14 | 初始PRD版本,完整算法细节与数据Schema | AI Assistant |