import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.user import UserProfile  # 假设你的模型在这个路径
from backend.models.question import Question


async def update_user_profile(
        db: AsyncSession,
        user_id: int,
        question: Question,
        is_correct: bool
):
    # 1. 获取或创建画像
    profile = await db.get(UserProfile, user_id)

    if not profile:
        profile = UserProfile(
            user_id=user_id,
            total_questions=0,
            correct_count=0,
            # 初始化为空字典
            knowledge_mastery={},
            weak_points={}
        )
        db.add(profile)
        # 如果是新创建，先提交一次以获取 ID (可选，视具体需求而定，这里为了简化逻辑暂不commit)

    # 2. 基础计数更新
    profile.total_questions += 1
    if is_correct:
        profile.correct_count += 1

    # 3. 安全加载 JSON 数据 (处理可能为 None 或字符串的情况)
    # 使用 profile 实例属性，SQLAlchemy 会自动处理 JSON 序列化/反序列化 (如果配置了 TypeDecorator)
    # 如果不确定是否自动转换，手动处理一下更稳妥：
    try:
        mastery = profile.knowledge_mastery if profile.knowledge_mastery else {}
        weaks = profile.weak_points if profile.weak_points else {}

        # 确保是字典类型 (防止数据库里存了奇怪的东西)
        if not isinstance(mastery, dict): mastery = {}
        if not isinstance(weaks, dict): weaks = {}
    except Exception:
        mastery = {}
        weaks = {}

    # 4. 获取题目知识点标签
    # 即使数据库里是 NULL，default=list 也会保证它是空列表 []
    topics = question.knowledge_points or []

    # 如果没有标签，就用一个默认标签 "未知"
    if not topics:
        topics = ["未知"]

    # 5. 核心算法：更新每个知识点的状态
    for topic in topics:
        # --- 更新掌握度 (Mastery) ---
        current_score = mastery.get(topic, 0.5)  # 默认初始掌握度 0.5

        if is_correct:
            # 做对了：分数增加，越接近 1.0 增加越慢 (避免溢出)
            increment = (1.0 - current_score) * 0.2
            new_score = min(1.0, current_score + increment)
        else:
            # 做错了：分数减少，越接近 0 减少越慢
            decrement = current_score * 0.3
            new_score = max(0.0, current_score - decrement)

        mastery[topic] = round(new_score, 2)  # 保留两位小数

        # --- 更新弱点 (Weak Points) ---
        if not is_correct:
            # 只有做错才增加弱点计数
            weaks[topic] = weaks.get(topic, 0) + 1
        else:
            # 做对了，可以选择让弱点计数轻微减少，或者保持不变
            # 这里选择保持不变，只记录历史错题总数，这样更直观
            pass

    # 6. 写回对象 (SQLAlchemy 通常会自动检测 JSON 变化，但显式赋值更保险)
    profile.knowledge_mastery = mastery
    profile.weak_points = weaks

    # 7. 提交事务
    await db.commit()
    await db.refresh(profile)

    return profile