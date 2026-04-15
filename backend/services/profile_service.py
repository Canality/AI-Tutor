import json
from typing import Dict, List, Optional, Literal, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.profile import UserProfile
from models.question import Question
from models.record import LearningRecord


# ==================== 掌握度计算策略 ====================

# 支持的策略类型
MASTERY_STRATEGY_SIMPLE = "simple"                          # 简单平均
MASTERY_STRATEGY_WEIGHTED_TIME_DECAY = "weighted_time_decay"  # 时间衰减加权
MASTERY_STRATEGY_EXPONENTIAL_SMOOTHING = "exponential_smoothing"  # 指数平滑

# 默认策略
DEFAULT_MASTERY_STRATEGY = MASTERY_STRATEGY_SIMPLE


def calculate_mastery_score(
    records: List[LearningRecord],
    strategy: Literal["simple", "weighted_time_decay", "exponential_smoothing"] = "simple",
    current_time: Optional[datetime] = None
) -> Dict[str, float]:
    """
    计算知识点掌握度分数 - 策略模式实现

    【功能说明】
    根据用户的学习记录，计算各个知识点的掌握度分数。
    支持多种计算策略，便于未来扩展和 A/B 测试。

    【策略说明】
    ====================
    1. simple (简单平均):
       直接计算正确率，不考虑时间因素。
       公式: 掌握度 = 正确答题数 / 总答题数

    2. weighted_time_decay (时间衰减加权):
       越近期的答题权重越高，体现学习进步。
       公式: 掌握度 = Σ(正确性 * 时间权重) / Σ(时间权重)
       时间权重: w = exp(-λ * (当前时间 - 答题时间))

    3. exponential_smoothing (指数平滑):
       使用指数平滑算法，更关注近期表现。
       公式: S_t = α * X_t + (1-α) * S_{t-1}
       其中 α 为平滑因子，X_t 为第 t 次答题结果 (1=正确, 0=错误)

    【参数说明】
    :param records: 学习记录列表
    :param strategy: 计算策略 ("simple", "weighted_time_decay", "exponential_smoothing")
    :param current_time: 当前时间 (用于时间衰减策略)

    :return: 知识点 -> 掌握度分数 的字典
    """
    if not records:
        return {}

    if strategy == MASTERY_STRATEGY_SIMPLE:
        return _calculate_mastery_simple(records)
    elif strategy == MASTERY_STRATEGY_WEIGHTED_TIME_DECAY:
        return _calculate_mastery_weighted_time_decay(records, current_time)
    elif strategy == MASTERY_STRATEGY_EXPONENTIAL_SMOOTHING:
        return _calculate_mastery_exponential_smoothing(records)
    else:
        raise ValueError(f"不支持的掌握度计算策略: {strategy}")


def _calculate_mastery_simple(records: List[LearningRecord]) -> Dict[str, float]:
    """
    简单平均策略：计算每个知识点的正确率

    【算法说明】
    对每个知识点，统计正确答题数和总答题数，计算正确率。
    不考虑时间因素，所有答题记录权重相同。
    """
    # 按知识点分组统计
    topic_stats: Dict[str, Dict[str, int]] = {}

    for record in records:
        # 获取题目知识点
        topics = _extract_knowledge_points(record)

        for topic in topics:
            if topic not in topic_stats:
                topic_stats[topic] = {"total": 0, "correct": 0}

            topic_stats[topic]["total"] += 1
            if record.is_correct:
                topic_stats[topic]["correct"] += 1

    # 计算掌握度
    mastery_scores = {}
    for topic, stats in topic_stats.items():
        if stats["total"] > 0:
            mastery_scores[topic] = round(stats["correct"] / stats["total"], 2)
        else:
            mastery_scores[topic] = 0.5  # 默认值

    return mastery_scores


def _calculate_mastery_weighted_time_decay(
    records: List[LearningRecord],
    current_time: Optional[datetime] = None,
    decay_half_life_days: float = 7.0
) -> Dict[str, float]:
    """
    时间衰减加权策略：近期答题权重更高

    【算法说明】
    使用指数衰减函数计算时间权重，越近期的答题对掌握度影响越大。
    半衰期默认为 7 天，即一周前的答题权重减半。

    【参数说明】
    :param decay_half_life_days: 半衰期（天），默认 7 天
    """
    if current_time is None:
        current_time = datetime.now()

    # 计算衰减系数 λ
    # 半衰期公式: 0.5 = exp(-λ * half_life) => λ = ln(2) / half_life
    lambda_decay = 0.693 / decay_half_life_days

    # 按知识点分组统计
    topic_data: Dict[str, List[tuple]] = {}  # topic -> [(is_correct, weight), ...]

    for record in records:
        topics = _extract_knowledge_points(record)

        # 计算时间权重
        record_time = record.created_at
        if record_time is None:
            weight = 1.0
        else:
            # 处理时区问题
            if record_time.tzinfo is None:
                record_time = record_time.replace(tzinfo=None)
            if current_time.tzinfo is not None:
                current_time = current_time.replace(tzinfo=None)

            days_diff = (current_time - record_time).total_seconds() / 86400
            weight = 2.718 ** (-lambda_decay * days_diff)  # exp(-λt)

        for topic in topics:
            if topic not in topic_data:
                topic_data[topic] = []

            is_correct_val = 1.0 if record.is_correct else 0.0
            topic_data[topic].append((is_correct_val, weight))

    # 计算加权掌握度
    mastery_scores = {}
    for topic, data in topic_data.items():
        weighted_sum = sum(score * weight for score, weight in data)
        weight_sum = sum(weight for _, weight in data)

        if weight_sum > 0:
            mastery_scores[topic] = round(weighted_sum / weight_sum, 2)
        else:
            mastery_scores[topic] = 0.5

    return mastery_scores


def _calculate_mastery_exponential_smoothing(
    records: List[LearningRecord],
    alpha: float = 0.3
) -> Dict[str, float]:
    """
    指数平滑策略：更关注近期表现

    【算法说明】
    使用指数平滑算法计算掌握度，每次新的答题结果按 α 比例更新掌握度。
    α 越大，新结果对掌握度的影响越大。

    【参数说明】
    :param alpha: 平滑因子 (0-1)，默认 0.3
    """
    # 按知识点分组，按时间排序
    topic_records: Dict[str, List[LearningRecord]] = {}

    for record in records:
        topics = _extract_knowledge_points(record)
        for topic in topics:
            if topic not in topic_records:
                topic_records[topic] = []
            topic_records[topic].append(record)

    # 对每个知识点应用指数平滑
    mastery_scores = {}
    for topic, topic_recs in topic_records.items():
        # 按时间排序
        sorted_recs = sorted(topic_recs, key=lambda r: r.created_at or datetime.min)

        # 初始掌握度
        mastery = 0.5

        for rec in sorted_recs:
            result = 1.0 if rec.is_correct else 0.0
            mastery = alpha * result + (1 - alpha) * mastery

        mastery_scores[topic] = round(mastery, 2)

    return mastery_scores


def _extract_knowledge_points(record: LearningRecord) -> List[str]:
    """
    从学习记录中提取知识点列表

    【功能说明】
    统一处理模式 A (系统题库) 和模式 B (用户上传) 两种数据来源。
    """
    topics = []

    if record.source_type == 'uploaded' and record.custom_question_data:
        # 模式 B: 从 custom_question_data 提取
        data = record.custom_question_data
        if isinstance(data, dict):
            kp = data.get('knowledge_points', [])
            if isinstance(kp, list):
                topics = [str(t) for t in kp if t]
            elif isinstance(kp, str):
                try:
                    topics = json.loads(kp)
                except:
                    topics = []
    elif record.question:
        # 模式 A: 从 question 关联对象提取
        kp = record.question.knowledge_points
        if isinstance(kp, list):
            topics = [str(t) for t in kp if t]
        elif isinstance(kp, str):
            try:
                topics = json.loads(kp)
            except:
                topics = []

    return topics if topics else ["未知知识点"]


# ==================== 用户画像服务 ====================


async def get_user_profile(db: AsyncSession, user_id: int) -> Dict:
    """
    获取用户的学习画像

    返回字典格式，方便 API 层直接使用

    【改进说明】
    - 使用 select().where() 查询 user_id 字段
    - 自动创建新用户画像（首次访问时）
    - 防御性编程：处理 None 值和空数据
    """
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        # 如果用户没有画像，返回默认空画像
        return {
            "user_id": user_id,
            "total_questions": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "knowledge_mastery": {},
            "weak_points": {},
            "theta_se": None,
            "theta_ci_lower": None,
            "theta_ci_upper": None,
            "avg_mastery": None,
            "weak_kp_count": 0,
            "learning_style": None,
            "mastery_strategy": DEFAULT_MASTERY_STRATEGY,
        }


    # 计算正确率（防止除以零）
    accuracy = 0.0
    if profile.total_questions > 0:
        accuracy = round((profile.correct_count / profile.total_questions) * 100, 2)

    return {
        "user_id": profile.user_id,
        "total_questions": profile.total_questions,
        "correct_count": profile.correct_count,
        "accuracy": accuracy,
        "knowledge_mastery": profile.knowledge_mastery or {},
        "weak_points": profile.weak_points or {},
        "theta_se": profile.theta_se,
        "theta_ci_lower": profile.theta_ci_lower,
        "theta_ci_upper": profile.theta_ci_upper,
        "avg_mastery": profile.avg_mastery,
        "weak_kp_count": profile.weak_kp_count or 0,
        "learning_style": profile.learning_style,
        "mastery_strategy": profile.mastery_strategy or DEFAULT_MASTERY_STRATEGY,
    }



async def get_user_profile_with_mastery(
    db: AsyncSession,
    user_id: int,
    mastery_strategy: str = DEFAULT_MASTERY_STRATEGY
) -> Dict:
    """
    获取用户画像（包含动态计算的掌握度）

    【功能说明】
    基于用户的学习记录，使用指定策略动态计算掌握度。
    这比存储在 profile 表中的静态掌握度更准确。

    【参数说明】
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param mastery_strategy: 掌握度计算策略

    :return: 包含动态掌握度的用户画像字典
    """
    # 获取基础画像
    profile = await get_user_profile(db, user_id)

    # 获取用户的学习记录
    stmt = select(LearningRecord).where(LearningRecord.user_id == user_id)
    result = await db.execute(stmt)
    records = result.scalars().all()

    # 使用指定策略计算掌握度
    dynamic_mastery = calculate_mastery_score(
        records=list(records),
        strategy=mastery_strategy
    )

    # 合并到画像中
    profile["knowledge_mastery_dynamic"] = dynamic_mastery
    profile["mastery_strategy"] = mastery_strategy

    return profile


async def update_user_profile(
    db: AsyncSession,
    user_id: int,
    question: Question,
    is_correct: bool
):
    """
    更新用户画像（答题后调用）

    【功能说明】
    - 动态计算知识点掌握度（非线性增长/衰减模型）
    - 记录薄弱点（错题统计）
    - 自动创建新用户画像（首次答题时）
    """
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        # 首次答题时自动创建用户画像
        profile = UserProfile(
            user_id=user_id,
            total_questions=0,
            correct_count=0,
            knowledge_mastery={},
            weak_points={}
        )
        db.add(profile)

    # 2. 基础计数更新
    profile.total_questions += 1
    if is_correct:
        profile.correct_count += 1

    # 3. 安全加载 JSON 数据
    try:
        mastery = profile.knowledge_mastery if profile.knowledge_mastery else {}
        weaks = profile.weak_points if profile.weak_points else {}

        if not isinstance(mastery, dict):
            mastery = {}
        if not isinstance(weaks, dict):
            weaks = {}
    except Exception:
        mastery = {}
        weaks = {}

    # 4. 获取题目知识点标签
    topics = question.knowledge_points or []
    if not topics:
        topics = ["未知"]

    # 5. 核心算法：更新每个知识点的状态
    # 非线性增长/衰减算法
    # 原理: 越接近满分，增长越慢；越接近零，衰减越慢
    # 做错扣分比例(0.3) > 做对加分比例(0.2)，体现"错题更值得关注"
    for topic in topics:
        # --- 更新掌握度 (Mastery) ---
        current_score = mastery.get(topic, 0.5)  # 默认初始掌握度 0.5（中等水平）

        if is_correct:
            # 做对：增长，但越接近 1.0 增长越慢
            increment = (1.0 - current_score) * 0.2
            new_score = min(1.0, current_score + increment)
        else:
            # 做错：衰减，但越接近 0 衰减越慢
            decrement = current_score * 0.3
            new_score = max(0.0, current_score - decrement)

        mastery[topic] = round(new_score, 2)

        # --- 更新弱点 (Weak Points) ---
        # 只有做错才增加弱点计数
        if not is_correct:
            weaks[topic] = weaks.get(topic, 0) + 1

    # 6. 写回对象
    profile.knowledge_mastery = mastery
    profile.weak_points = weaks

    # 7. 提交事务
    await db.commit()
    await db.refresh(profile)

    return profile
