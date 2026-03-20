from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from database.db import get_db
from services.recommendation_service import recommend_exercises

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.get("/recommend")
async def get_recommended_exercises(
    user_id: int = Query(..., description="用户ID (测试用)"),
    limit: int = Query(5, description="推荐数量", ge=1, le=20),
    algorithm_version: Optional[str] = Query(None, description="A/B 测试算法版本"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取推荐的练习题 (支持 A/B 测试)
    
    基于用户的薄弱知识点进行个性化推荐。
    可通过 algorithm_version 参数指定算法版本进行 A/B 测试。
    
    测试示例: GET /api/exercises/recommend?user_id=1&limit=5&algorithm_version=v2.0
    """
    try:
        recommendations = await recommend_exercises(db, user_id, limit, algorithm_version)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "count": len(recommendations),
                "exercises": recommendations
            }
        }
    except Exception as e:
        print(f"Error recommending exercises: {e}")
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.get("/plan")
async def get_study_plan(
    user_id: int = Query(..., description="用户ID (测试用)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取学习计划
    
    根据用户画像生成个性化学习计划
    
    测试示例: GET /api/exercises/plan?user_id=1
    """
    try:
        # 暂时返回简化版学习计划
        # 后续可以基于用户画像生成更详细的计划
        from services.profile_service import get_user_profile
        
        profile = await get_user_profile(db, user_id)
        
        # 基于薄弱点生成建议
        weak_points = profile.get("weak_points", {})
        suggestions = []
        
        if weak_points:
            # 按错误次数排序
            sorted_weaks = sorted(weak_points.items(), key=lambda x: x[1], reverse=True)
            for topic, count in sorted_weaks[:3]:  # 前3个薄弱点
                suggestions.append({
                    "topic": topic,
                    "error_count": count,
                    "suggestion": f"建议重点练习【{topic}】相关题目，当前错误次数：{count}"
                })
        else:
            suggestions.append({
                "topic": "综合",
                "error_count": 0,
                "suggestion": "您还没有答题记录，建议从基础题目开始练习"
            })
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "accuracy": profile.get("accuracy", 0),
                "total_questions": profile.get("total_questions", 0),
                "suggestions": suggestions
            }
        }
    except Exception as e:
        print(f"Error generating study plan: {e}")
        raise HTTPException(status_code=500, detail=f"生成学习计划失败: {str(e)}")
