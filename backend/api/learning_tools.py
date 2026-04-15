from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.user import User
from services.auth_service import get_current_user
from services.learning_analytics_service import (
    create_or_update_favorite,
    list_favorites,
    list_mistake_book,
    list_review_reminders,
    remove_favorite,
    upsert_mistake_book,
)
from models.learning_analytics import MistakeBook, Favorite
from sqlalchemy import and_, select
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/learning-tools", tags=["LearningTools"])


# ---------------------------------------------------------------------------
# 错题本
# ---------------------------------------------------------------------------

@router.get("/mistakes")
async def get_mistake_book(
    mastered: Optional[bool] = Query(None, description="是否仅查看已掌握/未掌握"),
    only_due: bool = Query(False, description="是否只看到期复习"),
    knowledge_point: Optional[str] = Query(None, description="按知识点筛选"),
    days: Optional[int] = Query(None, ge=1, le=365, description="按最近N天筛选"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户错题本"""
    try:
        rows = await list_mistake_book(
            db=db,
            user_id=current_user.id,
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
                    "mastered_at": row.mastered_at.isoformat() if row.mastered_at else None,
                    "review_count": row.review_count,
                    "last_review_at": row.last_review_at.isoformat() if row.last_review_at else None,
                    "next_review_at": row.next_review_at.isoformat() if row.next_review_at else None,
                    "first_error_at": row.first_error_at.isoformat() if row.first_error_at else None,
                    "last_error_at": row.last_error_at.isoformat() if row.last_error_at else None,
                    "knowledge_points": (q.knowledge_points if q else []),
                    "question_content": (q.content if q else None),
                    "standard_answer": (q.standard_answer if q else None),
                    "question_type": (q.question_type if q else None),
                    "difficulty": (q.difficulty if q else None),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
            )

        return {"success": True, "data": {"count": len(data), "items": data}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错题本失败: {str(e)}")


@router.get("/mistakes/stats")
async def get_mistake_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取错题本统计摘要"""
    try:
        from datetime import datetime
        from sqlalchemy import func as sqlfunc

        # 总数
        total_stmt = select(sqlfunc.count(MistakeBook.id)).where(
            MistakeBook.user_id == current_user.id
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # 未掌握
        unmastered_stmt = select(sqlfunc.count(MistakeBook.id)).where(
            and_(MistakeBook.user_id == current_user.id, MistakeBook.mastered == False)
        )
        unmastered_result = await db.execute(unmastered_stmt)
        unmastered = unmastered_result.scalar() or 0

        # 到期复习
        now = datetime.now()
        due_stmt = select(sqlfunc.count(MistakeBook.id)).where(
            and_(
                MistakeBook.user_id == current_user.id,
                MistakeBook.mastered == False,
                MistakeBook.next_review_at.is_not(None),
                MistakeBook.next_review_at <= now,
            )
        )
        due_result = await db.execute(due_stmt)
        due = due_result.scalar() or 0

        return {
            "success": True,
            "data": {
                "total": total,
                "unmastered": unmastered,
                "mastered": total - unmastered,
                "due_for_review": due,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.patch("/mistakes/{mistake_id}/master")
async def mark_mistake_mastered(
    mistake_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记错题为已掌握"""
    try:
        from datetime import datetime

        stmt = select(MistakeBook).where(
            and_(MistakeBook.id == mistake_id, MistakeBook.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="错题记录不存在")

        item.mastered = True
        item.mastered_at = datetime.now()
        await db.commit()

        return {"success": True, "message": "已标记为掌握"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.patch("/mistakes/{mistake_id}/unmaster")
async def mark_mistake_unmastered(
    mistake_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消已掌握标记（重新加入待复习）"""
    try:
        stmt = select(MistakeBook).where(
            and_(MistakeBook.id == mistake_id, MistakeBook.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="错题记录不存在")

        from datetime import datetime
        from services.learning_analytics_service import _compute_next_review_time

        item.mastered = False
        item.mastered_at = None
        item.next_review_at = _compute_next_review_time(item.error_count or 1, datetime.now())
        await db.commit()

        return {"success": True, "message": "已重新加入待复习"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.get("/mistakes/review-reminders")
async def get_review_reminders(
    window_days: int = Query(3, ge=1, le=30, description="未来提醒窗口天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取复习提醒（到期 + 即将到期）"""
    try:
        rows = await list_review_reminders(db=db, user_id=current_user.id, window_days=window_days)

        def serialize(items):
            result = []
            for row in items:
                q = row.question
                result.append(
                    {
                        "id": row.id,
                        "question_id": row.question_id,
                        "error_count": row.error_count,
                        "review_count": row.review_count,
                        "next_review_at": row.next_review_at.isoformat() if row.next_review_at else None,
                        "question_content": q.content if q else None,
                        "knowledge_points": q.knowledge_points if q else [],
                        "question_type": q.question_type if q else None,
                        "difficulty": q.difficulty if q else None,
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


# ---------------------------------------------------------------------------
# 收藏夹
# ---------------------------------------------------------------------------

@router.post("/favorites")
async def add_or_update_favorite(
    question_id: int = Query(..., description="题目ID"),
    folder_name: str = Query("默认收藏夹", description="收藏夹名称"),
    note: Optional[str] = Query(None, description="备注"),
    tags: Optional[List[str]] = Query(None, description="标签列表，可重复传入"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await create_or_update_favorite(
            db=db,
            user_id=current_user.id,
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
    folder_name: Optional[str] = Query(None, description="按收藏夹筛选"),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        items = await list_favorites(db=db, user_id=current_user.id, folder_name=folder_name, limit=limit)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        ok = await remove_favorite(db=db, user_id=current_user.id, favorite_id=favorite_id)
        if not ok:
            raise HTTPException(status_code=404, detail="收藏记录不存在")
        return {"success": True, "message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除收藏失败: {str(e)}")
