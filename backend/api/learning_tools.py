from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from services.learning_analytics_service import (
    create_or_update_favorite,
    list_favorites,
    list_mistake_book,
    list_review_reminders,
    remove_favorite,
)

router = APIRouter(prefix="/learning-tools", tags=["LearningTools"])


@router.get("/mistakes")
async def get_mistake_book(
    user_id: int = Query(..., description="用户ID (测试用)"),
    mastered: Optional[bool] = Query(None, description="是否仅查看已掌握/未掌握"),
    only_due: bool = Query(False, description="是否只看到期复习"),
    knowledge_point: Optional[str] = Query(None, description="按知识点筛选"),
    days: Optional[int] = Query(None, ge=1, le=365, description="按最近N天筛选"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await list_mistake_book(
            db=db,
            user_id=user_id,
            mastered=mastered,
            only_due=only_due,
            knowledge_point=knowledge_point,
            days=days,
            limit=limit,
        )

        data = []
        for row in rows:
            q = row.question
            data.append(
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "question_id": row.question_id,
                    "error_count": row.error_count,
                    "mastered": row.mastered,
                    "review_count": row.review_count,
                    "next_review_at": row.next_review_at.isoformat() if row.next_review_at else None,
                    "last_error_at": row.last_error_at.isoformat() if row.last_error_at else None,
                    "knowledge_points": (q.knowledge_points if q else []),
                    "question_content": (q.content if q else None),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
            )

        return {"success": True, "data": {"count": len(data), "items": data}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错题本失败: {str(e)}")


@router.get("/mistakes/review-reminders")
async def get_review_reminders(
    user_id: int = Query(..., description="用户ID (测试用)"),
    window_days: int = Query(3, ge=1, le=30, description="未来提醒窗口天数"),
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await list_review_reminders(db=db, user_id=user_id, window_days=window_days)

        def serialize(items):
            result = []
            for row in items:
                q = row.question
                result.append(
                    {
                        "id": row.id,
                        "question_id": row.question_id,
                        "error_count": row.error_count,
                        "next_review_at": row.next_review_at.isoformat() if row.next_review_at else None,
                        "question_content": q.content if q else None,
                        "knowledge_points": q.knowledge_points if q else [],
                    }
                )
            return result

        return {
            "success": True,
            "data": {
                "due": serialize(rows["due"]),
                "upcoming": serialize(rows["upcoming"]),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取复习提醒失败: {str(e)}")


@router.post("/favorites")
async def add_or_update_favorite(
    user_id: int = Query(..., description="用户ID (测试用)"),
    question_id: int = Query(..., description="题目ID"),
    folder_name: str = Query("默认收藏夹", description="收藏夹名称"),
    note: Optional[str] = Query(None, description="备注"),
    tags: Optional[List[str]] = Query(None, description="标签列表，可重复传入"),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_or_update_favorite(
            db=db,
            user_id=user_id,
            question_id=question_id,
            folder_name=folder_name,
            note=note,
            tags=tags,
        )
        return {
            "success": True,
            "data": {
                "id": item.id,
                "user_id": item.user_id,
                "question_id": item.question_id,
                "folder_name": item.folder_name,
                "note": item.note,
                "tags": item.tags or [],
                "created_at": item.created_at.isoformat() if item.created_at else None,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"收藏失败: {str(e)}")


@router.get("/favorites")
async def get_favorites(
    user_id: int = Query(..., description="用户ID (测试用)"),
    folder_name: Optional[str] = Query(None, description="按收藏夹筛选"),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    try:
        items = await list_favorites(db=db, user_id=user_id, folder_name=folder_name, limit=limit)
        data = [
            {
                "id": item.id,
                "question_id": item.question_id,
                "folder_name": item.folder_name,
                "note": item.note,
                "tags": item.tags or [],
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "question_content": item.question.content if item.question else None,
                "knowledge_points": item.question.knowledge_points if item.question else [],
            }
            for item in items
        ]
        return {"success": True, "data": {"count": len(data), "items": data}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取收藏夹失败: {str(e)}")


@router.delete("/favorites/{favorite_id}")
async def delete_favorite(
    favorite_id: int,
    user_id: int = Query(..., description="用户ID (测试用)"),
    db: AsyncSession = Depends(get_db),
):
    try:
        ok = await remove_favorite(db=db, user_id=user_id, favorite_id=favorite_id)
        if not ok:
            raise HTTPException(status_code=404, detail="收藏记录不存在")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除收藏失败: {str(e)}")
