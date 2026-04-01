from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.db import get_db
from schemas.question import CustomQuestionPayload
from services.record_service import save_uploaded_question_record, RecordValidationError

router = APIRouter(prefix="/upload")


@router.post("/image")
async def upload_image():
    """图片上传端点（占位符）"""
    return {"message": "Upload image endpoint"}


@router.post("/question")
async def upload_question(
    content: str,
    user_answer: str,
    standard_answer: Optional[str] = None,
    difficulty: int = 2,
    question_type: str = "short_answer",
    knowledge_points: Optional[str] = None,  # 逗号分隔的知识点
    user_id: int = 1,  # 实际应从 JWT token 获取
    db: AsyncSession = Depends(get_db)
):
    """
    上传自定义题目并保存学习记录
    
    - **content**: 题目内容
    - **user_answer**: 用户答案
    - **standard_answer**: 标准答案（可选）
    - **difficulty**: 难度 1-5，默认 2
    - **question_type**: 题型，默认 short_answer
    - **knowledge_points**: 知识点，逗号分隔（可选）
    """
    try:
        # 解析知识点
        kp_list = []
        if knowledge_points:
            kp_list = [k.strip() for k in knowledge_points.split(",") if k.strip()]
        
        # 构建 payload
        payload = CustomQuestionPayload(
            content=content,
            standard_answer=standard_answer,
            difficulty=difficulty,
            question_type=question_type,
            knowledge_points=kp_list,
            user_answer=user_answer
        )
        
        # 保存记录
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")
