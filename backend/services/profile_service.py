import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.user import UserProfile
from backend.models.question import Question


async def get_user_profile(db: AsyncSession, user_id: int):
    """
    获取用户的学习画像
    返回字典格式，方便 API 层直接使用
    
    [成员E开发 2026-03-18]:
    - 使用 select().where() 查询 user_id 字段
    - 自动创建新用户画像（首次访问时）
    - 防御性编程：处理 None 值和空数据
    """
    # [成员E修复 2026-03-18]: 使用 select().where() 替代 db.get()
    # 原因: db.get(Model, id) 查询的是主键 id，而 UserProfile 表的主键是自增 id
    #       用户关联的是 user_id 外键，必须使用 where 条件查询
    # 示例: 用户A的 user_id=100，但 profile 记录的 id 可能是 5
    #       如果用 db.get(UserProfile, 100)，会查到 id=100 的记录（可能不存在或属于其他用户）
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        # [成员E设计]: 如果用户没有画像，返回默认空画像
        # 不自动创建数据库记录，保持查询操作的纯粹性
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
    
    [成员E开发 2026-03-18]:
    - 动态计算知识点掌握度（非线性增长/衰减模型）
    - 记录薄弱点（错题统计）
    - 自动创建新用户画像（首次答题时）
    """
    # [成员E修复 2026-03-18]: 使用 select().where() 替代 db.get()
    # 原因: 同 get_user_profile，必须通过 user_id 外键查询
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        # [成员E设计]: 首次答题时自动创建用户画像
        # 与 get_user_profile 不同，这里需要持久化到数据库
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
    # [成员E设计]: 防御性编程，处理可能的 None 或非法值
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
    # [成员E设计]: 非线性增长/衰减算法
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
