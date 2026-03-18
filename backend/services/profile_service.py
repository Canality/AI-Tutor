import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.user import UserProfile
from backend.models.question import Question


async def get_user_profile(db: AsyncSession, user_id: int):
    """
    获取用户的学习画像
    返回字典格式，方便 API 层直接使用
    """
    # 【关键修正】使用 select 通过 user_id 查找，而不是主键 id
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        # 如果用户没有画像，返回一个默认的空画像
        return {
            "user_id": user_id,
            "total_questions": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "knowledge_mastery": {},
            "weak_points": {}
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
        "weak_points": profile.weak_points or {}
    }


async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        question: Question,
        is_correct: bool
):
    """
    更新用户画像（答题后调用）
    """
    # 获取或创建画像对象
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
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
    for topic in topics:
        # --- 更新掌握度 (Mastery) ---
        current_score = mastery.get(topic, 0.5)

        if is_correct:
            increment = (1.0 - current_score) * 0.2
            new_score = min(1.0, current_score + increment)
        else:
            decrement = current_score * 0.3
            new_score = max(0.0, current_score - decrement)

        mastery[topic] = round(new_score, 2)

        # --- 更新弱点 (Weak Points) ---
        if not is_correct:
            weaks[topic] = weaks.get(topic, 0) + 1

    # 6. 写回对象
    profile.knowledge_mastery = mastery
    profile.weak_points = weaks

    # 7. 提交事务
    await db.commit()
    await db.refresh(profile)

    return profile
