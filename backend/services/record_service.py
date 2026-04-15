"""
学习记录服务模块

提供学习记录的创建、查询等功能，支持双模态数据存储：
- 模式 A: 系统题库题 (question_id 关联)
- 模式 B: 用户上传题 (custom_question_data 存储)
"""

from typing import Optional, Dict, Any, Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.record import LearningRecord
from models.question import Question
from schemas.question import CustomQuestionData, CustomQuestionPayload


class RecordValidationError(Exception):
    """学习记录校验错误"""
    pass


async def save_learning_record(
    db: AsyncSession,
    user_id: int,
    question_obj: Optional[Question] = None,
    custom_question_payload: Optional[CustomQuestionPayload] = None,
    answer: str = "",
    is_correct: Optional[bool] = None,
    source_type: Literal['recommended', 'practice', 'uploaded'] = 'recommended',
    recommendation_algorithm_version: Optional[str] = None,
    recommendation_session_id: Optional[str] = None,
    hint_count: int = 0,
    time_spent: Optional[int] = None,
    skip_reason: Optional[Literal['too_easy', 'too_hard', 'other']] = None,
    theta_before: Optional[float] = None,
    theta_after: Optional[float] = None,
    mastery_updates: Optional[Dict[str, Any]] = None,
) -> LearningRecord:

    """
    保存学习记录 - 双模态存储支持

    【双模态校验规则】
    ===================
    模式 A (source_type = 'recommended' 或 'practice'):
        - question_obj 必须提供 (系统题库题对象)
        - custom_question_payload 必须为 None
        - is_correct 必须提供 (布尔值)

    模式 B (source_type = 'uploaded'):
        - question_obj 必须为 None
        - custom_question_payload 必须提供 (CustomQuestionPayload)
        - is_correct 可选 (用户上传题可能无标准答案)

    【参数说明】
    ===================
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param question_obj: 系统题库题对象 (模式 A 必填)
    :param custom_question_payload: 用户上传题数据 (模式 B 必填)
    :param answer: 用户答案
    :param is_correct: 是否正确 (模式 A 必填，模式 B 可选)
    :param source_type: 来源类型 ('recommended', 'practice', 'uploaded')
    :param recommendation_algorithm_version: 推荐算法版本 (A/B 测试用)

    :return: 创建的 LearningRecord 对象
    :raises RecordValidationError: 当双模态校验失败时抛出
    """

    # ==================== 双模态校验逻辑 ====================

    if source_type in ('recommended', 'practice'):
        # --- 模式 A 校验 ---
        if question_obj is None:
            raise RecordValidationError(
                f"模式 A (source_type='{source_type}') 要求提供 question_obj (系统题库题对象)"
            )
        if custom_question_payload is not None:
            raise RecordValidationError(
                f"模式 A (source_type='{source_type}') 不允许提供 custom_question_payload"
            )
        if is_correct is None:
            raise RecordValidationError(
                f"模式 A (source_type='{source_type}') 要求提供 is_correct (布尔值)"
            )

        # 模式 A: 使用系统题库题数据
        question_id = question_obj.id
        custom_question_data = None

    elif source_type == 'uploaded':
        # --- 模式 B 校验 ---
        if question_obj is not None:
            raise RecordValidationError(
                "模式 B (source_type='uploaded') 不允许提供 question_obj"
            )
        if custom_question_payload is None:
            raise RecordValidationError(
                "模式 B (source_type='uploaded') 要求提供 custom_question_payload"
            )

        # 模式 B: 使用用户上传题数据
        question_id = None
        # 转换为 CustomQuestionData 并序列化为字典
        custom_data_obj = custom_question_payload.to_custom_question_data()
        custom_question_data = custom_data_obj.model_dump()

        # 如果提供了 answer 参数，优先使用；否则使用 payload 中的 user_answer
        if not answer and custom_question_payload.user_answer:
            answer = custom_question_payload.user_answer

    else:
        raise RecordValidationError(
            f"无效的 source_type: '{source_type}'。"
            f"允许的值为: 'recommended', 'practice', 'uploaded'"
        )

    # ==================== 创建记录 ====================

    record = LearningRecord(
        user_id=user_id,
        question_id=question_id,
        source_type=source_type,
        custom_question_data=custom_question_data,
        user_answer=answer,
        is_correct=is_correct,
        recommendation_session_id=recommendation_session_id,
        recommendation_algorithm_version=recommendation_algorithm_version,
        hint_count=max(0, hint_count or 0),
        time_spent=time_spent,
        skip_reason=skip_reason,
        theta_before=theta_before,
        theta_after=theta_after,
        mastery_updates=mastery_updates,
    )


    db.add(record)
    await db.commit()
    await db.refresh(record)

    return record


async def save_uploaded_question_record(
    db: AsyncSession,
    user_id: int,
    payload: CustomQuestionPayload,
    is_correct: Optional[bool] = None,
    ai_feedback: Optional[str] = None
) -> LearningRecord:
    """
    保存用户上传题目的学习记录 (模式 B 的便捷方法)

    这是 save_learning_record 的封装，专门用于处理用户上传题。
    自动设置 source_type='uploaded' 并进行必要的校验。

    【使用场景】
    - 用户上传图片/文本题目并作答
    - AI 评估用户答案后保存记录

    【参数说明】
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param payload: 用户上传题数据 (已校验)
    :param is_correct: 是否正确 (可选，AI 评估后可补充)
    :param ai_feedback: AI 反馈/解析 (可选)

    :return: 创建的 LearningRecord 对象
    """
    record = await save_learning_record(
        db=db,
        user_id=user_id,
        question_obj=None,
        custom_question_payload=payload,
        answer=payload.user_answer,
        is_correct=is_correct,
        source_type='uploaded'
    )

    # 如果有 AI 反馈，更新记录
    if ai_feedback:
        record.ai_feedback = ai_feedback
        await db.commit()
        await db.refresh(record)

    return record


async def save_recommended_question_record(
    db: AsyncSession,
    user_id: int,
    question: Question,
    answer: str,
    is_correct: bool,
    recommendation_algorithm_version: Optional[str] = None,
    recommendation_session_id: Optional[str] = None,
    hint_count: int = 0,
    time_spent: Optional[int] = None,
    skip_reason: Optional[Literal['too_easy', 'too_hard', 'other']] = None,
    theta_before: Optional[float] = None,
    theta_after: Optional[float] = None,
    mastery_updates: Optional[Dict[str, Any]] = None,
) -> LearningRecord:

    """
    保存系统推荐题目的学习记录 (模式 A 的便捷方法)

    这是 save_learning_record 的封装，专门用于处理系统推荐题。
    自动设置 source_type='recommended' 并进行必要的校验。

    【使用场景】
    - 用户完成系统推荐的练习题
    - 需要记录推荐算法版本以支持 A/B 测试

    【参数说明】
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param question: 系统题库题对象
    :param answer: 用户答案
    :param is_correct: 是否正确
    :param recommendation_algorithm_version: 推荐算法版本 (A/B 测试用)
    :param recommendation_session_id: 推荐会话 ID

    :return: 创建的 LearningRecord 对象
    """
    record = await save_learning_record(
        db=db,
        user_id=user_id,
        question_obj=question,
        custom_question_payload=None,
        answer=answer,
        is_correct=is_correct,
        source_type='recommended',
        recommendation_algorithm_version=recommendation_algorithm_version,
        recommendation_session_id=recommendation_session_id,
        hint_count=hint_count,
        time_spent=time_spent,
        skip_reason=skip_reason,
        theta_before=theta_before,
        theta_after=theta_after,
        mastery_updates=mastery_updates,
    )


    return record



async def get_learning_history(
    db: AsyncSession,
    user_id: int,
    limit: Optional[int] = None,
    offset: int = 0,
    source_type: Optional[str] = None
) -> list[LearningRecord]:
    """
    获取用户的学习历史

    【参数说明】
    :param db: 数据库会话
    :param user_id: 用户 ID
    :param limit: 返回记录数量限制
    :param offset: 分页偏移量
    :param source_type: 按来源类型过滤 (可选)

    :return: LearningRecord 对象列表
    """
    # 构建查询
    stmt = (
        select(LearningRecord)
        .where(LearningRecord.user_id == user_id)
        .options(joinedload(LearningRecord.question))
        .order_by(LearningRecord.created_at.desc())
    )

    # 添加过滤条件
    if source_type:
        stmt = stmt.where(LearningRecord.source_type == source_type)

    # 添加分页
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().unique())


async def get_learning_record_by_id(
    db: AsyncSession,
    record_id: int,
    user_id: Optional[int] = None
) -> Optional[LearningRecord]:
    """
    根据 ID 获取学习记录

    【参数说明】
    :param db: 数据库会话
    :param record_id: 记录 ID
    :param user_id: 用户 ID (可选，用于权限校验)

    :return: LearningRecord 对象，不存在则返回 None
    """
    stmt = (
        select(LearningRecord)
        .where(LearningRecord.id == record_id)
        .options(joinedload(LearningRecord.question))
    )

    if user_id is not None:
        stmt = stmt.where(LearningRecord.user_id == user_id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def extract_question_data(record: LearningRecord) -> Dict[str, Any]:
    """
    从学习记录中提取题目数据 (统一接口)

    无论题目来源是系统题库还是用户上传，都返回统一格式的题目数据。

    【返回格式】
    {
        "id": int or None,
        "content": str,
        "standard_answer": str or None,
        "difficulty": int,
        "question_type": str,
        "knowledge_points": list,
        "source_type": str
    }
    """
    if record.source_type == 'uploaded' and record.custom_question_data:
        # 模式 B: 从 custom_question_data 提取
        data = record.custom_question_data
        return {
            "id": None,
            "content": data.get("content", ""),
            "standard_answer": data.get("standard_answer"),
            "difficulty": data.get("difficulty", 2),
            "question_type": data.get("question_type", "short_answer"),
            "knowledge_points": data.get("knowledge_points", []),
            "source_type": "uploaded"
        }
    elif record.question:
        # 模式 A: 从 question 关联对象提取
        return {
            "id": record.question.id,
            "content": record.question.content,
            "standard_answer": record.question.standard_answer,
            "difficulty": record.question.difficulty or 2,
            "question_type": record.question.question_type or "short_answer",
            "knowledge_points": record.question.knowledge_points or [],
            "source_type": record.source_type
        }
    else:
        # 异常情况：既没有 custom_question_data 也没有 question
        return {
            "id": None,
            "content": "[题目数据不可用]",
            "standard_answer": None,
            "difficulty": 2,
            "question_type": "unknown",
            "knowledge_points": [],
            "source_type": record.source_type
        }
