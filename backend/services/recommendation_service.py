import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.user import UserProfile
from backend.models.question import Question
from backend.models.record import LearningRecord


async def recommend_exercises(db: AsyncSession, user_id: int, limit: int = 5):
    """
    基于用户弱点动态推荐题目
    :param db: 数据库会话
    :param user_id: 用户ID
    :param limit: 推荐题目的数量上限
    :return: List[Dict] 推荐题目列表
    """

    # 1. 获取用户画像（使用 select 查询 user_id 字段）
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

        # 按错误次数排序，优先推荐错得最多的知识点
        sorted_topics = sorted(weak_data.items(), key=lambda x: x[1], reverse=True)
        target_topics = [topic for topic, count in sorted_topics]
    except Exception:
        return []

    if not target_topics:
        return []

    # 3. 查询候选题目（内存中筛选）
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
            "type": q.type,
            "content": q.content,
            "difficulty": q.difficulty,
            "knowledge_points": q.knowledge_points or [],
            "image_url": q.image_url
        })

    return recommended_list
