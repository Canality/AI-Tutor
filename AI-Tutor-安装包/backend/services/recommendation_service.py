import json
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.profile import UserProfile
from models.question import Question
from models.record import LearningRecord
from services.record_service import save_recommended_question_record


# ==================== A/B 测试配置 ====================

# 推荐算法版本常量
RECOMMENDATION_ALGORITHM_V1 = "v1.0"           # 基础版本：按弱点排序
RECOMMENDATION_ALGORITHM_V2 = "v2.0"           # 实验版本：可添加新策略
RECOMMENDATION_ALGORITHM_CONTROL = "control"   # 对照组
RECOMMENDATION_ALGORITHM_TREATMENT = "treatment"  # 实验组

# 默认算法版本
DEFAULT_ALGORITHM_VERSION = RECOMMENDATION_ALGORITHM_V1


async def recommend_exercises(
    db: AsyncSession,
    user_id: int,
    limit: int = 5,
    algorithm_version: Optional[str] = None
) -> List[Dict]:
    """
    基于用户弱点动态推荐题目 (支持 A/B 测试)

    【A/B 测试支持】
    ===================
    通过 algorithm_version 参数可以指定不同的推荐算法版本，
    用于对比不同算法的效果。

    支持的版本:
    - "v1.0": 基础版本，按弱点错误次数排序
    - "v2.0": 实验版本 (预留，可扩展新策略)
    - "control": 对照组
    - "treatment": 实验组

    【参数说明】
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param limit: 推荐题目的数量上限
    :param algorithm_version: 推荐算法版本 (A/B 测试用)

    :return: 推荐题目列表，每个题目包含 algorithm_version 字段
    """

    # 使用默认版本（如果未指定）
    if algorithm_version is None:
        algorithm_version = DEFAULT_ALGORITHM_VERSION

    # 1. 获取用户画像
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile or not profile.weak_points:
        # 如果没有弱点，返回空列表（后续可以改为推荐基础题）
        return []

    # 2. 解析弱点数据
    try:
        weak_data = profile.weak_points
        if isinstance(weak_data, str):
            weak_data = json.loads(weak_data)

        # 根据算法版本选择排序策略
        if algorithm_version in (RECOMMENDATION_ALGORITHM_V2, RECOMMENDATION_ALGORITHM_TREATMENT):
            # 实验版本：可以添加新的排序逻辑，例如考虑掌握度
            sorted_topics = _sort_topics_v2(weak_data, profile.knowledge_mastery)
        else:
            # 基础版本：按错误次数排序
            sorted_topics = _sort_topics_v1(weak_data)

        target_topics = [topic for topic, count in sorted_topics]
    except Exception:
        return []

    if not target_topics:
        return []

    # 3. 查询候选题目
    stmt = select(Question).where(
        Question.knowledge_points.isnot(None)
    )
    result = await db.execute(stmt)
    all_questions = result.scalars().all()

    # 内存中筛选：只要题目的知识点列表和目标弱点有交集
    candidate_questions = []
    for q in all_questions:
        q_topics = q.knowledge_points or []
        if isinstance(q_topics, str):
            try:
                q_topics = json.loads(q_topics)
            except:
                q_topics = []

        # 检查是否有交集
        if any(topic in q_topics for topic in target_topics):
            candidate_questions.append(q)

    # 4. 排除已做过的题目（最近50道）
    recent_records_stmt = select(LearningRecord.question_id).where(
        LearningRecord.user_id == user_id
    ).order_by(LearningRecord.created_at.desc()).limit(50)

    recent_result = await db.execute(recent_records_stmt)
    done_question_ids = {row[0] for row in recent_result.fetchall() if row[0] is not None}

    # 过滤掉做过的题
    final_questions = [q for q in candidate_questions if q.id not in done_question_ids]

    # 5. 排序与截断
    final_questions.sort(key=lambda x: x.difficulty or 1)
    final_questions = final_questions[:limit]

    # 6. 转换为字典格式返回
    recommended_list = []
    for q in final_questions:
        recommended_list.append({
            "id": q.id,
            "type": q.question_type,
            "content": q.content,
            "difficulty": q.difficulty,
            "knowledge_points": q.knowledge_points or [],
            "image_url": None,  # 预留字段，后续支持图片题
            "algorithm_version": algorithm_version  # 记录算法版本
        })

    return recommended_list


def _sort_topics_v1(weak_data: Dict[str, int]) -> List[tuple]:
    """
    基础排序策略：按错误次数降序排列

    【策略说明】
    优先推荐用户错得最多的知识点相关的题目。
    """
    return sorted(weak_data.items(), key=lambda x: x[1], reverse=True)


def _sort_topics_v2(weak_data: Dict[str, int], mastery_data: Optional[Dict]) -> List[tuple]:
    """
    实验排序策略：综合考虑错误次数和掌握度

    【策略说明】
    在错误次数的基础上，结合掌握度进行加权排序。
    掌握度越低且错误次数越多的知识点优先级越高。

    【计算公式】
    优先级分数 = 错误次数 * (1 - 掌握度)

    例如:
    - 知识点 A: 错误 5 次, 掌握度 0.3 -> 分数 = 5 * 0.7 = 3.5
    - 知识点 B: 错误 3 次, 掌握度 0.8 -> 分数 = 3 * 0.2 = 0.6
    - 结果: A 的优先级高于 B
    """
    if mastery_data is None:
        mastery_data = {}

    if isinstance(mastery_data, str):
        try:
            mastery_data = json.loads(mastery_data)
        except:
            mastery_data = {}

    scored_topics = []
    for topic, error_count in weak_data.items():
        mastery = mastery_data.get(topic, 0.5)  # 默认掌握度 0.5
        if not isinstance(mastery, (int, float)):
            mastery = 0.5

        # 计算优先级分数
        priority_score = error_count * (1 - mastery)
        scored_topics.append((topic, priority_score))

    # 按优先级分数降序排列
    scored_topics.sort(key=lambda x: x[1], reverse=True)
    return [(topic, score) for topic, score in scored_topics]


async def record_recommendation_result(
    db: AsyncSession,
    user_id: int,
    question_id: int,
    user_answer: str,
    is_correct: bool,
    algorithm_version: str,
    recommendation_session_id: Optional[str] = None
) -> LearningRecord:
    """
    记录推荐题目的答题结果 (带 A/B 测试追踪)

    【功能说明】
    当用户完成一道推荐题目后，调用此函数保存学习记录。
    会自动记录 algorithm_version 以支持 A/B 测试效果分析。

    【参数说明】
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param question_id: 题目 ID
    :param user_answer: 用户答案
    :param is_correct: 是否正确
    :param algorithm_version: 推荐算法版本
    :param recommendation_session_id: 推荐会话 ID (可选)

    :return: 创建的 LearningRecord 对象
    """
    # 获取题目对象
    stmt = select(Question).where(Question.id == question_id)
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()

    if not question:
        raise ValueError(f"题目不存在: question_id={question_id}")

    # 保存学习记录，包含算法版本
    record = await save_recommended_question_record(
        db=db,
        user_id=user_id,
        question=question,
        answer=user_answer,
        is_correct=is_correct,
        recommendation_algorithm_version=algorithm_version,
        recommendation_session_id=recommendation_session_id
    )

    return record


async def get_recommendation_ab_test_stats(
    db: AsyncSession,
    algorithm_version: str,
    limit: int = 1000
) -> Dict:
    """
    获取 A/B 测试统计数据

    【功能说明】
    统计指定算法版本的推荐效果指标，用于 A/B 测试分析。

    【返回指标】
    - total_records: 总记录数
    - correct_count: 正确答题数
    - accuracy: 正确率
    - avg_difficulty: 平均题目难度

    【参数说明】
    :param db: 数据库会话
    :param algorithm_version: 算法版本
    :param limit: 最大统计记录数

    :return: 统计数据字典
    """
    stmt = select(LearningRecord).where(
        LearningRecord.recommendation_algorithm_version == algorithm_version
    ).limit(limit)

    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return {
            "algorithm_version": algorithm_version,
            "total_records": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "avg_difficulty": 0.0
        }

    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    accuracy = correct / total if total > 0 else 0.0

    return {
        "algorithm_version": algorithm_version,
        "total_records": total,
        "correct_count": correct,
        "accuracy": round(accuracy, 4),
        "avg_difficulty": 0.0  # 可以扩展计算平均难度
    }
