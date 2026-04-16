"""
Redis管理API
提供Redis核心数据结构的CRUD接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from services.redis_service import get_redis_service, RedisService

router = APIRouter(prefix="/redis", tags=["Redis Core Data Structures"])


# ============ 请求/响应模型 ============

class SeenQuestionRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    question_id: str = Field(..., description="题目ID")


class SeenQuestionsBatchRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    question_ids: List[str] = Field(..., description="题目ID列表")


class ReviewQueueRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    question_id: str = Field(..., description="题目ID")
    error_count: int = Field(default=1, description="错误次数")


class MasteryRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    knowledge_point_id: str = Field(..., description="知识点ID")
    score: int = Field(..., ge=0, le=100, description="掌握度分数(0-100)")


class MasteriesBatchRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    masteries: Dict[str, int] = Field(..., description="知识点掌握度字典")


class SessionRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    data: Dict = Field(default_factory=dict, description="会话数据")
    expire_seconds: int = Field(default=3600, description="过期时间(秒)")


class UserStateResponse(BaseModel):
    user_id: int
    seen_count: int
    review_count: int
    due_reviews: List[Dict]
    masteries: Dict[str, int]
    weak_points: List[tuple]


# ============ Seen Pool API ============

@router.post("/seen/add", summary="添加已做题目")
async def add_seen_question(request: SeenQuestionRequest):
    """添加单个题目到已做题目池"""
    try:
        service = get_redis_service()
        result = service.add_seen_question(request.user_id, request.question_id)
        return {
            "success": True,
            "user_id": request.user_id,
            "question_id": request.question_id,
            "is_new": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seen/add-batch", summary="批量添加已做题目")
async def add_seen_questions_batch(request: SeenQuestionsBatchRequest):
    """批量添加题目到已做题目池"""
    try:
        service = get_redis_service()
        count = service.add_seen_questions(request.user_id, request.question_ids)
        return {
            "success": True,
            "user_id": request.user_id,
            "added_count": count,
            "question_ids": request.question_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seen/check/{user_id}/{question_id}", summary="检查题目是否已做")
async def check_question_seen(user_id: int, question_id: str):
    """检查题目是否已在已做题目池中"""
    try:
        service = get_redis_service()
        is_seen = service.is_question_seen(user_id, question_id)
        return {
            "user_id": user_id,
            "question_id": question_id,
            "is_seen": is_seen
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seen/{user_id}", summary="获取所有已做题目")
async def get_seen_questions(user_id: int):
    """获取用户的所有已做题目"""
    try:
        service = get_redis_service()
        questions = service.get_seen_questions(user_id)
        count = service.get_seen_count(user_id)
        return {
            "user_id": user_id,
            "count": count,
            "question_ids": list(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/seen/{user_id}/{question_id}", summary="移除已做题目")
async def remove_seen_question(user_id: int, question_id: str):
    """从已做题目池中移除指定题目"""
    try:
        service = get_redis_service()
        result = service.remove_seen_question(user_id, question_id)
        return {
            "success": True,
            "user_id": user_id,
            "question_id": question_id,
            "removed": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Review Queue API ============

@router.post("/review/add", summary="添加题目到复习队列")
async def add_to_review_queue(request: ReviewQueueRequest):
    """
    添加题目到错题复习队列
    
    根据错误次数自动计算下次复习时间（Spaced Repetition）
    """
    try:
        service = get_redis_service()
        next_review_at = service.add_to_review_queue(
            request.user_id,
            request.question_id,
            request.error_count
        )
        from datetime import datetime
        return {
            "success": True,
            "user_id": request.user_id,
            "question_id": request.question_id,
            "error_count": request.error_count,
            "next_review_at": next_review_at,
            "next_review_time": datetime.fromtimestamp(next_review_at).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/due/{user_id}", summary="获取到期复习题目")
async def get_due_reviews(user_id: int, limit: int = 10):
    """获取已到期的复习题目"""
    try:
        service = get_redis_service()
        reviews = service.get_due_reviews(user_id, limit)
        return {
            "user_id": user_id,
            "count": len(reviews),
            "due_reviews": [item.to_dict() for item in reviews]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/{user_id}", summary="获取所有复习题目")
async def get_all_reviews(user_id: int):
    """获取用户的所有复习队列中的题目"""
    try:
        service = get_redis_service()
        reviews = service.get_all_reviews(user_id)
        count = service.get_review_count(user_id)
        return {
            "user_id": user_id,
            "count": count,
            "reviews": [item.to_dict() for item in reviews]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/review/{user_id}/{question_id}", summary="移除复习题目")
async def remove_from_review_queue(user_id: int, question_id: str):
    """从复习队列中移除指定题目"""
    try:
        service = get_redis_service()
        result = service.remove_from_review_queue(user_id, question_id)
        return {
            "success": True,
            "user_id": user_id,
            "question_id": question_id,
            "removed": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/update-error-count", summary="更新错误次数")
async def update_review_error_count(request: ReviewQueueRequest):
    """
    更新题目的错误次数并重新计算复习时间
    
    用于再次做错题目时推迟复习时间
    """
    try:
        service = get_redis_service()
        next_review_at = service.update_review_error_count(
            request.user_id,
            request.question_id,
            request.error_count
        )
        from datetime import datetime
        return {
            "success": True,
            "user_id": request.user_id,
            "question_id": request.question_id,
            "error_count": request.error_count,
            "next_review_at": next_review_at,
            "next_review_time": datetime.fromtimestamp(next_review_at).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Mastery Hash API ============

@router.post("/mastery/set", summary="设置知识点掌握度")
async def set_mastery(request: MasteryRequest):
    """设置单个知识点的掌握度"""
    try:
        service = get_redis_service()
        service.set_mastery(
            request.user_id,
            request.knowledge_point_id,
            request.score
        )
        return {
            "success": True,
            "user_id": request.user_id,
            "knowledge_point_id": request.knowledge_point_id,
            "score": request.score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mastery/set-batch", summary="批量设置掌握度")
async def set_masteries_batch(request: MasteriesBatchRequest):
    """批量设置知识点掌握度"""
    try:
        service = get_redis_service()
        service.set_masteries(request.user_id, request.masteries)
        return {
            "success": True,
            "user_id": request.user_id,
            "count": len(request.masteries),
            "masteries": request.masteries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery/{user_id}/{knowledge_point_id}", summary="获取知识点掌握度")
async def get_mastery(user_id: int, knowledge_point_id: str):
    """获取指定知识点的掌握度"""
    try:
        service = get_redis_service()
        score = service.get_mastery(user_id, knowledge_point_id)
        if score is None:
            return {
                "user_id": user_id,
                "knowledge_point_id": knowledge_point_id,
                "score": None,
                "message": "该知识点掌握度未设置"
            }
        return {
            "user_id": user_id,
            "knowledge_point_id": knowledge_point_id,
            "score": score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery/{user_id}", summary="获取所有掌握度")
async def get_all_masteries(user_id: int):
    """获取用户的所有知识点掌握度"""
    try:
        service = get_redis_service()
        masteries = service.get_all_masteries(user_id)
        return {
            "user_id": user_id,
            "count": len(masteries),
            "masteries": masteries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery/{user_id}/weak", summary="获取薄弱知识点")
async def get_weak_knowledge_points(user_id: int, threshold: int = 50):
    """
    获取薄弱知识点（掌握度低于阈值）
    
    用于Advisor推荐时优先选择薄弱知识点
    """
    try:
        service = get_redis_service()
        weak_points = service.get_weak_knowledge_points(user_id, threshold)
        return {
            "user_id": user_id,
            "threshold": threshold,
            "count": len(weak_points),
            "weak_points": [
                {"knowledge_point_id": kp, "score": score}
                for kp, score in weak_points
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/mastery/{user_id}/{knowledge_point_id}", summary="删除掌握度")
async def delete_mastery(user_id: int, knowledge_point_id: str):
    """删除指定知识点的掌握度"""
    try:
        service = get_redis_service()
        result = service.delete_mastery(user_id, knowledge_point_id)
        return {
            "success": True,
            "user_id": user_id,
            "knowledge_point_id": knowledge_point_id,
            "deleted": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Session API ============

@router.post("/session/set", summary="设置Session数据")
async def set_session_data(request: SessionRequest):
    """设置Session状态数据"""
    try:
        service = get_redis_service()
        service.set_session_data(
            request.session_id,
            request.data,
            request.expire_seconds
        )
        return {
            "success": True,
            "session_id": request.session_id,
            "expire_seconds": request.expire_seconds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", summary="获取Session数据")
async def get_session_data(session_id: str):
    """获取Session状态数据"""
    try:
        service = get_redis_service()
        data = service.get_session_data(session_id)
        return {
            "session_id": session_id,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}", summary="删除Session")
async def delete_session(session_id: str):
    """删除Session"""
    try:
        service = get_redis_service()
        result = service.delete_session(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "deleted": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 综合查询 API ============

@router.get("/state/{user_id}", summary="获取用户完整学习状态", response_model=UserStateResponse)
async def get_user_learning_state(user_id: int):
    """
    获取用户完整学习状态
    
    用于Advisor推题前快速获取用户画像
    """
    try:
        service = get_redis_service()
        state = service.get_user_learning_state(user_id)
        return UserStateResponse(**state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 管理 API ============

@router.delete("/clear/{user_id}", summary="清空用户所有Redis数据")
async def clear_all_user_data(user_id: int):
    """清空用户的所有Redis数据（用于测试）"""
    try:
        service = get_redis_service()
        service.clear_all_user_data(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "message": "所有Redis数据已清空"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Redis健康检查")
async def redis_health_check():
    """检查Redis连接状态"""
    try:
        service = get_redis_service()
        service.redis_client.ping()
        info = service.redis_client.info()
        return {
            "status": "healthy",
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human")
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis连接异常: {str(e)}")
