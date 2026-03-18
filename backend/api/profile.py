from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from services.profile_service import get_user_profile

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/")
async def get_profile(
    user_id: int = Query(..., description="用户ID (测试用，后续将改为从登录态获取)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的学习画像
    
    [成员E开发 2026-03-18]:
    - 临时使用 Query 参数传递 user_id，便于开发和测试
    - 后续接入认证系统后，改为从 JWT Token 中获取当前用户
    
    测试示例: GET /api/profile?user_id=1
    
    返回包含以下信息：
    - total_questions: 总答题数
    - correct_count: 正确答题数
    - accuracy: 正确率（百分比）
    - knowledge_mastery: 各知识点掌握度
    - weak_points: 薄弱知识点
    """
    try:
        # [成员E设计]: 调用 Service 层获取画像数据
        # Service 层负责业务逻辑，API 层负责 HTTP 协议处理
        profile_data = await get_user_profile(db, user_id)
        
        # [成员E设计]: 统一响应格式，便于前端处理
        return {
            "success": True,
            "data": profile_data
        }
    except Exception as e:
        # [成员E设计]: 打印错误日志到控制台，方便调试
        # 生产环境建议使用 logger 替代 print
        print(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=f"获取画像失败: {str(e)}")
