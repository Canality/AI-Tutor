"""
Advisor Agent API 路由
-----------------------
GET  /api/advisor/init         — 初始化画像（首次/重建）
GET  /api/advisor/recommend    — 获取推荐题目（含 Advisor 模式和推荐理由）
POST /api/advisor/feedback     — 提交答题反馈（更新画像 + Redis 写回）
GET  /api/advisor/profile      — 获取带 Redis 缓存的快速画像
GET  /api/advisor/redis/health — Redis 健康检查
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent.advisor import (
    get_advisor_recommendations,
    init_user_profile,
    record_answer_feedback,
)
from database.db import get_db
from models.user import User
from services.auth_service import get_current_user
from utils import redis_client as rc
from utils.logger import logger

router = APIRouter(prefix="/advisor", tags=["Advisor"])


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class FeedbackPayload(BaseModel):
    question_id: int = Field(..., description="题目ID")
    is_correct: bool = Field(..., description="是否答对")
    hint_count: int = Field(0, ge=0, description="使用提示次数")
    time_spent: Optional[int] = Field(None, ge=0, description="答题耗时(秒)")
    skip_reason: Optional[str] = Field(
        None,
        description="跳过原因：too_easy / too_hard / other",
        pattern="^(too_easy|too_hard|other)$",
    )
    algorithm_version: str = Field("advisor-v1", description="推荐算法版本")
    recommendation_session_id: Optional[str] = Field(None, description="推荐会话ID")


# ---------------------------------------------------------------------------
# 初始化画像
# ---------------------------------------------------------------------------

@router.get("/init")
async def init_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    初始化用户画像（含 Redis 同步）

    - 首次使用时调用
    - 也可用于强制重建 Redis 缓存
    """
    try:
        profile = await init_user_profile(db, current_user.id)
        return {"success": True, "data": profile}
    except Exception as e:
        logger.error(f"[Advisor API] init_profile failed uid={current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"画像初始化失败: {e}")


# ---------------------------------------------------------------------------
# 获取推荐题目
# ---------------------------------------------------------------------------

@router.get("/recommend")
async def advisor_recommend(
    limit: int = Query(5, ge=1, le=10, description="推荐数量"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Advisor 推荐题目接口

    - 优先推送到期复习题（Redis Review ZSet）
    - 其余推送针对薄弱知识点的新题（去重后）
    - 返回 Advisor 模式、推荐理由和教学策略控制参数
    """
    try:
        result = await get_advisor_recommendations(db, current_user.id, limit=limit)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"[Advisor API] recommend failed uid={current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"推荐失败: {e}")


# ---------------------------------------------------------------------------
# 答题反馈
# ---------------------------------------------------------------------------

@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    提交答题反馈

    - 标记已做 -> Redis Seen Set
    - 更新 BKT/IRT -> MySQL + Redis Mastery Hash
    - 更新复习队列 -> Redis Review ZSet
    - 失效画像缓存（下次推荐时重新加载）

    跳过行为处理：
    - skip_reason=too_easy  -> Actual=1.0, θ+=0.1, 建议升级难度
    - skip_reason=too_hard  -> Actual=0.0, θ-=0.05, 建议降级难度
    """
    try:
        result = await record_answer_feedback(
            db=db,
            user_id=current_user.id,
            question_id=payload.question_id,
            is_correct=payload.is_correct,
            hint_count=payload.hint_count,
            time_spent=payload.time_spent,
            skip_reason=payload.skip_reason,
            algorithm_version=payload.algorithm_version,
            recommendation_session_id=payload.recommendation_session_id,
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"[Advisor API] feedback failed uid={current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"反馈提交失败: {e}")


# ---------------------------------------------------------------------------
# 快速画像查询
# ---------------------------------------------------------------------------

@router.get("/profile")
async def get_cached_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户画像（优先读取 Redis 缓存，降级读 MySQL）
    """
    try:
        cached = await rc.profile_cache_get(current_user.id)
        if cached:
            return {"success": True, "source": "redis_cache", "data": cached}
        # 降级：重新初始化（会写入缓存）
        profile = await init_user_profile(db, current_user.id)
        return {"success": True, "source": "mysql_rebuilt", "data": profile}
    except Exception as e:
        logger.error(f"[Advisor API] get_profile failed uid={current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取画像失败: {e}")


# ---------------------------------------------------------------------------
# Redis 健康检查
# ---------------------------------------------------------------------------

@router.get("/redis/health")
async def redis_health():
    """检查 Redis 连接状态"""
    ok = await rc.redis_ping()
    return {
        "redis_available": ok,
        "message": "Redis 连接正常" if ok else "Redis 不可用，系统将降级使用 MySQL",
    }
