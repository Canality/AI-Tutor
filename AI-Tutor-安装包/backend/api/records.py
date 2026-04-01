from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.db import get_db
from schemas.question import CustomQuestionPayload
from services.record_service import (
    save_uploaded_question_record,
    save_recommended_question_record,
    get_learning_history,
    extract_question_data,
    RecordValidationError
)

router = APIRouter(prefix="/records", tags=["学习记录"])


@router.post("/upload", response_model=dict)
async def upload_question_record(
    payload: CustomQuestionPayload,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    用户上传题目并保存学习记录
    
    接收用户上传的题目数据和答案，进行严格的 Schema 校验后保存。
    这是模式 B (source_type='uploaded') 的主要入口。
    """
    try:
        record = await save_uploaded_question_record(
            db=db,
            user_id=user_id,
            payload=payload,
            is_correct=None
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
    user_id: int,
    algorithm_version: Optional[str] = None,
    recommendation_session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    提交推荐题目的答案
    
    用户完成系统推荐的题目后，提交答案并保存学习记录。
    这是模式 A (source_type='recommended') 的主要入口。
    """
    try:
        from services.recommendation_service import record_recommendation_result
        
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
    user_id: int,
    limit: Optional[int] = 20,
    offset: int = 0,
    source_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户学习历史
    
    查询用户的学习记录，支持分页和按来源类型过滤。
    """
    records = await get_learning_history(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        source_type=source_type
    )

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
