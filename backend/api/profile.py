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
    
    测试示例: GET /api/profile?user_id=1
    """
    try:
        # 调用 Service 层
        profile_data = await get_user_profile(db, user_id)
        
        return {
            "success": True,
            "data": profile_data
        }
    except Exception as e:
        # 打印错误日志到控制台，方便调试
        print(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=f"获取画像失败: {str(e)}")
