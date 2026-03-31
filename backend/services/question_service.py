from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.question import Question
from schemas.question import QuestionCreate, QuestionUpdate


async def create_question(
    db: AsyncSession,
    user_id: int,
    payload: QuestionCreate,
) -> Question:
    question = Question(
        user_id=user_id,
        content=payload.content,
        standard_answer=payload.standard_answer,
        difficulty=payload.difficulty,
        question_type=payload.question_type,
        knowledge_points=payload.knowledge_points,
    )
    db.add(question)
    await db.flush()
    await db.refresh(question)
    return question


async def list_questions(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> Sequence[Question]:
    stmt = (
        select(Question)
        .where(Question.user_id == user_id)
        .order_by(Question.created_at.desc(), Question.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_question_by_id(
    db: AsyncSession,
    question_id: int,
    user_id: int,
) -> Optional[Question]:
    stmt = select(Question).where(
        Question.id == question_id,
        Question.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_question(
    db: AsyncSession,
    question: Question,
    payload: QuestionUpdate,
) -> Question:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    await db.flush()
    await db.refresh(question)
    return question


async def delete_question(
    db: AsyncSession,
    question: Question,
) -> None:
    await db.delete(question)
