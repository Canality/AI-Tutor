"""
认知诊断API接口
提供BKT、IRT、Actual Score等算法的REST API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from services.cognitive_diagnosis_service import (
    cognitive_service,
    update_mastery_after_answer,
    get_user_theta,
    compute_actual_score
)

router = APIRouter(prefix="/cognitive", tags=["cognitive-diagnosis"])


# ============ 请求/响应模型 ============

class MasteryUpdateRequest(BaseModel):
    """更新掌握度请求"""
    user_id: int = Field(..., description="用户ID")
    knowledge_point_id: int = Field(..., description="知识点ID")
    is_correct: bool = Field(..., description="是否答对")


class MasteryUpdateResponse(BaseModel):
    """更新掌握度响应"""
    user_id: int
    knowledge_point_id: int
    p_known: float = Field(..., description="更新后的掌握度")
    mastery_level: str = Field(..., description="掌握度等级: mastered/learning/weak")


class ThetaEstimateResponse(BaseModel):
    """能力值估计响应"""
    user_id: int
    theta: float = Field(..., description="最终能力值", ge=-3, le=3)
    theta_irt: float = Field(..., description="IRT估计值")
    theta_bkt: float = Field(..., description="BKT映射值")
    alpha: float = Field(..., description="K-IRT权重", ge=0, le=1)
    theta_se: float = Field(..., description="标准误")
    ci_lower: float = Field(..., description="置信区间下限")
    ci_upper: float = Field(..., description="置信区间上限")


class ActualScoreRequest(BaseModel):
    """计算Actual Score请求"""
    is_correct: bool = Field(..., description="是否正确")
    hint_level: int = Field(..., description="提示等级 0-4", ge=0, le=4)
    time_spent: float = Field(..., description="实际耗时(秒)", gt=0)
    expected_time: float = Field(..., description="期望耗时(秒)", gt=0)
    skip_reason: Optional[str] = Field(None, description="跳过原因")


class ActualScoreResponse(BaseModel):
    """计算Actual Score响应"""
    actual_score: float = Field(..., description="实际得分", ge=0, le=1)
    hint_level_name: str = Field(..., description="提示等级名称")
    components: dict = Field(..., description="分数组成部分")


class DifficultyRangeResponse(BaseModel):
    """推荐难度范围响应"""
    theta: float = Field(..., description="当前能力值")
    min_difficulty: float = Field(..., description="最小难度", ge=-3, le=3)
    max_difficulty: float = Field(..., description="最大难度", ge=-3, le=3)
    recommended_range: str = Field(..., description="推荐范围描述")


class ComprehensiveReportResponse(BaseModel):
    """综合诊断报告响应"""
    user_id: int
    ability: dict = Field(..., description="能力值信息")
    mastery_distribution: dict = Field(..., description="掌握度分布")
    recommended_difficulty: dict = Field(..., description="推荐难度范围")
    generated_at: str = Field(..., description="生成时间")


class MemoryDecayRequest(BaseModel):
    """应用记忆衰减请求"""
    user_id: int = Field(..., description="用户ID")


class MemoryDecayResponse(BaseModel):
    """应用记忆衰减响应"""
    user_id: int
    updated_count: int = Field(..., description="更新的知识点数量")
    updates: List[dict] = Field(..., description="更新详情")


# ============ API端点 ============

@router.post("/mastery/update", response_model=MasteryUpdateResponse)
async def api_update_mastery(
    request: MasteryUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新知识点掌握度（BKT算法）
    
    根据答题结果使用贝叶斯知识追踪算法更新掌握度
    """
    try:
        p_known = await update_mastery_after_answer(
            db,
            request.user_id,
            request.knowledge_point_id,
            request.is_correct
        )
        
        mastery_level = cognitive_service.get_mastery_level(p_known)
        
        return MasteryUpdateResponse(
            user_id=request.user_id,
            knowledge_point_id=request.knowledge_point_id,
            p_known=round(p_known, 4),
            mastery_level=mastery_level
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新掌握度失败: {str(e)}")


@router.get("/theta/{user_id}", response_model=ThetaEstimateResponse)
async def api_get_theta(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取学生能力值估计（K-IRT联合估算）
    
    使用K-IRT算法联合估算学生能力值
    """
    try:
        theta_info = await get_user_theta(db, user_id)
        
        return ThetaEstimateResponse(
            user_id=user_id,
            **theta_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"估计能力值失败: {str(e)}")


@router.post("/actual-score/calculate", response_model=ActualScoreResponse)
async def api_calculate_actual_score(request: ActualScoreRequest):
    """
    计算Actual Score（实际得分）
    
    根据答题正确性、提示等级、耗时计算实际得分
    
    提示等级说明：
    - 0: 自主完成 (权重1.0)
    - 1: 方向提示 (权重0.8)
    - 2: 公式提示 (权重0.6)
    - 3: 步骤推导 (权重0.4)
    - 4: 完整答案 (权重0.1)
    """
    try:
        score = await compute_actual_score(
            is_correct=request.is_correct,
            hint_level=request.hint_level,
            time_spent=request.time_spent,
            expected_time=request.expected_time,
            skip_reason=request.skip_reason
        )
        
        # 获取提示等级名称
        hint_names = {
            0: "自主完成",
            1: "方向提示",
            2: "公式提示",
            3: "步骤推导",
            4: "完整答案"
        }
        
        # 计算各组成部分（用于展示）
        from algorithms.actual_score import ActualScoreCalculator, AnswerRecord, HintLevel
        calc = ActualScoreCalculator()
        record = AnswerRecord(
            is_correct=request.is_correct,
            hint_level=HintLevel(request.hint_level),
            time_spent=request.time_spent,
            expected_time=request.expected_time,
            skip_reason=request.skip_reason
        )
        
        components = {
            "correctness": request.is_correct,
            "hint_weight": calc.params.hint_weights[HintLevel(request.hint_level)],
            "time_ratio": round(request.time_spent / request.expected_time, 2),
            "skip_reason": request.skip_reason
        }
        
        return ActualScoreResponse(
            actual_score=round(score, 4),
            hint_level_name=hint_names.get(request.hint_level, "未知"),
            components=components
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算Actual Score失败: {str(e)}")


@router.get("/difficulty-range/{user_id}", response_model=DifficultyRangeResponse)
async def api_get_difficulty_range(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取推荐题目难度范围
    
    基于学生能力值推荐合适的题目难度范围 [theta-0.5, theta+0.5]
    """
    try:
        theta_info = await get_user_theta(db, user_id)
        theta = theta_info['theta']
        
        min_diff, max_diff = cognitive_service.get_recommended_difficulty_range(theta)
        
        return DifficultyRangeResponse(
            theta=theta,
            min_difficulty=min_diff,
            max_difficulty=max_diff,
            recommended_range=f"[{min_diff:+.1f}, {max_diff:+.1f}]"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取难度范围失败: {str(e)}")


@router.get("/report/{user_id}", response_model=ComprehensiveReportResponse)
async def api_get_comprehensive_report(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取综合诊断报告
    
    包含能力值、掌握度分布、推荐难度等完整信息
    """
    try:
        report = await cognitive_service.get_comprehensive_report(db, user_id)
        return ComprehensiveReportResponse(**report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.post("/memory-decay/apply", response_model=MemoryDecayResponse)
async def api_apply_memory_decay(
    request: MemoryDecayRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    应用记忆衰减（艾宾浩斯遗忘曲线）
    
    对所有知识点应用遗忘曲线计算，更新掌握度
    """
    try:
        updates = await cognitive_service.apply_memory_decay(db, request.user_id)
        
        return MemoryDecayResponse(
            user_id=request.user_id,
            updated_count=len(updates),
            updates=updates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用记忆衰减失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "cognitive-diagnosis",
        "algorithms": ["BKT", "IRT", "K-IRT", "Adaptive-K", "Memory-Decay", "Actual-Score"]
    }
