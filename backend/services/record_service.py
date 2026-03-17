from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.record import LearningRecord
from backend.models.question import Question
import json


async def save_learning_record(
        db: AsyncSession,
        user_id: int,
        question_obj: Question = None,  # 如果是题库题，传入对象；否则为 None
        custom_question_text: str = None,  # 如果是上传题，传入文本
        answer: str = "",
        is_correct: bool = None,
        source_type: str = 'recommended'
):
    # 准备数据
    q_id = question_obj.id if question_obj else None

    custom_data = None
    if not question_obj and custom_question_text:
        custom_data = {
            "question_text": custom_question_text,
            "tags": ["uploaded"]
        }

    record = LearningRecord(
        user_id=user_id,
        question_id=q_id,  # 使用正确的字段名
        source_type=source_type,  # 明确来源
        custom_question_data=custom_data,  # 存入 JSON
        user_answer=answer,
        is_correct=is_correct
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


from sqlalchemy.orm import joinedload


async def get_learning_history(db: AsyncSession, user_id: int):
    # 预加载 question 和 user 关系，避免 N+1 问题
    stmt = (
        select(LearningRecord)
        .where(LearningRecord.user_id == user_id)
        .options(joinedload(LearningRecord.question))  # 一次性把题目信息也查出来
        .order_by(LearningRecord.created_at.desc())  # 按时间倒序，最近的在前面
    )

    result = await db.execute(stmt)
    return result.scalars().unique().all()  # 使用 unique() 防止因 join 产生的重复行