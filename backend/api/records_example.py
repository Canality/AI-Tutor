"""
学习记录 API 路由示例

本文件展示如何在 API 层使用新的 Pydantic Schema 进行数据校验。
实际项目中，请将此代码整合到现有的 api/records.py 或类似文件中。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.db import get_db
from schemas.question import CustomQuestionPayload, QuestionResponse
from services.record_service import (
    save_uploaded_question_record,
    save_recommended_question_record,
    get_learning_history,
    extract_question_data,
    RecordValidationError
)
from services.recommendation_service import (
    recommend_exercises,
    record_recommendation_result
)

# 创建路由（实际使用时请整合到现有路由）
router = APIRouter(prefix="/api/records", tags=["学习记录"])


@router.post("/upload", response_model=dict)
async def upload_question_record(
    payload: CustomQuestionPayload,
    user_id: int,  # 实际应从 JWT token 获取
    db: AsyncSession = Depends(get_db)
):
    """
    用户上传题目并保存学习记录

    【功能说明】
    接收用户上传的题目数据和答案，进行严格的 Schema 校验后保存。
    这是模式 B (source_type='uploaded') 的主要入口。

    【校验说明】
    - content: 必填，1-10000 字符
    - standard_answer: 可选，最多 5000 字符
    - difficulty: 1-5 整数，默认 2
    - question_type: 枚举值，默认 "short_answer"
    - knowledge_points: 字符串列表，最多 20 个，自动去重去空
    - user_answer: 必填，1-10000 字符

    【请求示例】
    ```json
    {
        "content": "解方程: 2x + 5 = 13",
        "standard_answer": "x = 4",
        "difficulty": 2,
        "question_type": "short_answer",
        "knowledge_points": ["方程", "一元一次方程"],
        "user_answer": "x = 4"
    }
    ```
    """
    try:
        # 保存学习记录
        record = await save_uploaded_question_record(
            db=db,
            user_id=user_id,
            payload=payload,
            is_correct=None  # 可由 AI 评估后更新
        )

        return {
            "success": True,
            "record_id": record.id,
            "message": "题目上传成功"
        }

    except RecordValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存失败: {str(e)}"
        )


@router.post("/recommended/{question_id}/submit", response_model=dict)
async def submit_recommended_answer(
    question_id: int,
    answer: str,
    is_correct: bool,
    user_id: int,  # 实际应从 JWT token 获取
    algorithm_version: Optional[str] = None,
    recommendation_session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    提交推荐题目的答案

    【功能说明】
    用户完成系统推荐的题目后，提交答案并保存学习记录。
    这是模式 A (source_type='recommended') 的主要入口。

    【A/B 测试支持】
    - algorithm_version: 推荐算法版本，用于追踪不同算法的效果
    - recommendation_session_id: 推荐会话 ID，用于关联同一批推荐

    【请求示例】
    ```json
    {
        "answer": "x = 4",
        "is_correct": true,
        "algorithm_version": "v2.0",
        "recommendation_session_id": "session_12345"
    }
    ```
    """
    try:
        record = await record_recommendation_result(
            db=db,
            user_id=user_id,
            question_id=question_id,
            user_answer=answer,
            is_correct=is_correct,
            algorithm_version=algorithm_version or "v1.0",
            recommendation_session_id=recommendation_session_id
        )

        return {
            "success": True,
            "record_id": record.id,
            "algorithm_version": record.recommendation_algorithm_version,
            "message": "答题记录已保存"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存失败: {str(e)}"
        )


@router.get("/history", response_model=list)
async def get_user_learning_history(
    user_id: int,  # 实际应从 JWT token 获取
    limit: Optional[int] = 20,
    offset: int = 0,
    source_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户学习历史

    【功能说明】
    查询用户的学习记录，支持分页和按来源类型过滤。
    返回的数据包含统一的题目格式，无论来源是系统题库还是用户上传。

    【参数说明】
    - limit: 返回记录数量，默认 20
    - offset: 分页偏移量
    - source_type: 过滤来源类型 ('uploaded', 'recommended', 'practice')
    """
    records = await get_learning_history(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        source_type=source_type
    )

    # 转换为统一格式
    result = []
    for record in records:
        question_data = extract_question_data(record)
        result.append({
            "record_id": record.id,
            "source_type": record.source_type,
            "user_answer": record.user_answer,
            "is_correct": record.is_correct,
            "ai_feedback": record.ai_feedback,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "question": question_data,
            "recommendation_algorithm_version": record.recommendation_algorithm_version
        })

    return result


@router.get("/recommendations", response_model=list)
async def get_recommendations(
    user_id: int,  # 实际应从 JWT token 获取
    limit: int = 5,
    algorithm_version: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取推荐题目 (支持 A/B 测试)

    【功能说明】
    基于用户弱点动态推荐题目，支持通过 algorithm_version 参数指定算法版本。

    【A/B 测试说明】
    - v1.0: 基础版本，按弱点错误次数排序
    - v2.0: 实验版本，综合考虑错误次数和掌握度
    - control: 对照组
    - treatment: 实验组

    【响应示例】
    ```json
    [
        {
            "id": 123,
            "type": "short_answer",
            "content": "解方程: 2x + 5 = 13",
            "difficulty": 2,
            "knowledge_points": ["方程", "一元一次方程"],
            "image_url": null,
            "algorithm_version": "v2.0"
        }
    ]
    ```
    """
    recommendations = await recommend_exercises(
        db=db,
        user_id=user_id,
        limit=limit,
        algorithm_version=algorithm_version
    )

    return recommendations
