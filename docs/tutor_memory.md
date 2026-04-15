我给你设计一套**完全兼容现有AI Tutor V3架构**的**Tutor记忆层**，以**短期会话记忆+中期交互记忆+长期画像记忆**三层结构，实现**实时动态更新用户画像**，直接可接入你现有PRD，不破坏原有BKT/IRT/Redis/MySQL逻辑。

# AI Tutor V3 新增：Tutor记忆层（动态用户画像更新）
## 一、核心定位与目标
- **定位**：独立于认知诊断引擎的**动态记忆模块**，捕捉用户**情绪、节奏、易错点、偏好、挫败感**等非答题数据，实时修正用户画像
- **目标**：让画像从**静态答题统计**变成**动态学习状态**，精准调控推题难度、提示等级、教学语气、复习策略
- **兼容**：完全复用现有Redis/MySQL表结构，仅做**字段扩展**与**新增记忆表**，不重构原有引擎

---

## 二、三层记忆架构（按时效分级，动态更新）
### 1. 短期记忆（Session级，实时生效）
- **时效**：当前学习会话（单轮做题/对话）
- **存储**：Redis Hash（高速读写，会话结束销毁）
- **作用**：实时感知当前状态，即时调整Instructor教学方式
- **更新频率**：每一次交互（答题/点击提示/发言/跳过）立即更新

### 2. 中期记忆（交互级，7天有效期）
- **时效**：近7天所有学习交互
- **存储**：Redis ZSet+Hash（定期持久化）
- **作用**：捕捉高频易错点、情绪波动、学习节奏，修正IRT能力值θ
- **更新频率**：每完成1个学习单元批量更新

### 3. 长期记忆（画像级，永久存储）
- **时效**：全周期学习历史
- **存储**：MySQL新增记忆表+原有user_profiles扩展
- **作用**：固化用户**学习风格、稳定易错点、认知偏好**，写入核心用户画像
- **更新频率**：每日凌晨异步批量更新

---

## 三、记忆层采集维度（4类动态特征，直接更新画像）
记忆层只采集**原有引擎未覆盖**的动态特征，不重复采集答题数据：
1. **情绪记忆**：挫败/烦躁/自信/厌倦（关键词检测）
2. **步骤易错记忆**：固定步骤反复错（如计算、公式、推导）
3. **节奏记忆**：答题快慢、提示依赖度、跳过频率
4. **偏好记忆**：喜欢的提示等级、厌恶的题型、接受的难度

---

## 四、记忆层数据结构设计（兼容原PRD）
### （一）Redis记忆Key设计（扩展原有Key-Schema）
| 记忆层级 | Key命名 | 数据结构 | 存储内容 | TTL |
| --- | --- | --- | --- | --- |
| 短期会话记忆 | ai:tutor:memory:session:{sid} | Hash | 情绪、当前易错步骤、提示次数、节奏 | 会话结束删除 |
| 中期交互记忆 | ai:tutor:memory:short:{uid} | Hash | 7天情绪统计、高频易错点、提示偏好 | 7天 |
| 长期记忆索引 | ai:tutor:memory:long:{uid} | Set | 稳定易错知识点、学习风格标签 | 永久 |

### （二）MySQL表扩展（不破坏原有结构）
#### 1. 原有表字段扩展（最小改动）
**user_profiles 新增动态画像字段**
```sql
-- 记忆层扩展字段
ALTER TABLE user_profiles
ADD COLUMN memory_mood VARCHAR(20) NULL, -- 主流情绪：frustrated/confident/bored
ADD COLUMN memory_error_steps JSON NULL, -- 高频易错步骤
ADD COLUMN memory_hint_prefer INT NULL, -- 偏好提示等级L1-L4
ADD COLUMN memory_learning_pace VARCHAR(20) NULL; -- 节奏：fast/medium/slow
```

**user_knowledge_mastery 新增动态修正字段**
```sql
ALTER TABLE user_knowledge_mastery
ADD COLUMN memory_adjust_score FLOAT DEFAULT 0.0; -- 记忆修正的掌握度偏移
```

#### 2. 新增长期记忆表（user_memory）
```sql
CREATE TABLE user_memory (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  memory_type ENUM('mood','error_step','hint_prefer','pace') NOT NULL,
  content JSON NOT NULL, -- 记忆内容
  update_count INT DEFAULT 1, -- 更新次数
  last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_type (user_id, memory_type)
);
```

---

## 五、动态更新用户画像规则（核心算法）
### 1. 短期记忆→实时修正当前教学（Instructor）
**触发条件**：用户发言/点击提示/连续步骤错/表达挫败
**更新动作**：
- 检测到“好难/看不懂”→**memory_mood=frustrated**→强制切换`MODE_ENCOURAGE`
- 检测到连续步骤错→**memory_error_steps记录**→Instructor自动展开该步骤
- 频繁点L3提示→**memory_hint_prefer=3**→提升提示等级优先级

### 2. 中期记忆→修正IRT/BKT参数（核心计算引擎）
**触发条件**：累计交互≥5次/会话结束
**更新公式**（兼容原有K-IRT）：
$$\theta_{final} = \alpha×\theta_{IRT} + (1-\alpha)×\theta_{BKT} + \theta_{memory}$$
- $\theta_{memory}$：记忆修正项（情绪挫败-0.1，自信+0.1，节奏慢-0.05）
- BKT掌握度修正：$P(L)_{new} = P(L)_{old} + memory\_adjust\_score$

### 3. 长期记忆→固化用户画像（Advisor）
**触发条件**：同一特征连续出现≥7天
**更新动作**：
- 高频错“计算步骤”→标记`calculation_error_prone`→Agent自动加计算提醒
- 偏好L2公式提示→默认提示等级设为L2
- 频繁跳过简单题→学习风格设为`aggressive`→优先推难题

---

## 六、记忆层与原有模块联动（全链路打通）
### 1. 与核心计算引擎联动
- 记忆层输出**修正系数**→注入IRT/BKT→动态调整难度区间$S_{next}$
- 错题复习队列：记忆层标记**高频易错点**→提升复习优先级

### 2. 与Instructor（讲师Agent）联动
- 读取短期记忆→自动调整**步骤详略、提示等级、语气**
- 情绪记忆→匹配引导话术，避免用户挫败

### 3. 与Advisor（顾问Agent）联动
- 读取中期/长期记忆→**个性化推题**（避开厌恶题型、匹配偏好难度）
- 记忆画像→生成更精准的推荐理由

---

## 七、极简落地步骤（1天可接入）
1. **扩展字段**：执行上述MySQL ALTER语句
2. **新增Redis Key**：接入3类记忆Key，复用原有Redis客户端
3. **接入采集**：在对话/答题/提示/跳过接口，加入记忆采集逻辑
4. **注入更新**：在画像更新、推题、教学响应环节，加入记忆修正
5. **异步持久化**：会话结束→短期→中期；每日→中期→长期

---

## 八、效果示例
- 用户连续3题错“一元二次方程求根步骤”→记忆层记录→下次遇到该知识点，Instructor**自动分步讲解**，Advisor**优先推步骤题**
- 用户频繁说“太简单”→记忆层标记**aggressive风格**→推题难度直接+0.5，提示等级降为L1
- 用户答题极慢、频繁用提示→记忆层标记**slow pace**→降低难度、增加提示次数、延长答题时间限制

要不要我把这段记忆层直接写成**可插入你原PRD的正式章节**（含LaTeX公式、SQL、伪代码），直接替换到文档里？