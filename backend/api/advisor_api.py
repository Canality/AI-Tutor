"""
Advisor Agent API
提供Advisor指令生成和教学模式管理接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple

from agents.advisor_agent import (
    get_advisor_agent, 
    AdvisorAgent, 
    UserLearningState, 
    AdvisorMode
)

router = APIRouter(prefix="/advisor", tags=["Advisor Agent"])


# ============ 请求/响应模型 ============

class UserStateRequest(BaseModel):
    """用户学习状态请求"""
    user_id: int = Field(..., description="用户ID")
    theta: float = Field(default=0.0, description="能力值")
    p_known: float = Field(default=0.5, description="当前知识点掌握度")
    consecutive_correct: int = Field(default=0, description="连续正确次数")
    consecutive_wrong: int = Field(default=0, description="连续错误次数")
    recent_accuracy: float = Field(default=0.5, description="近期正确率")
    weak_knowledge_points: List[Tuple[str, int]] = Field(
        default_factory=list, 
        description="薄弱知识点列表[(知识点ID, 分数)]"
    )
    recent_sentiment: str = Field(default="", description="近期情感状态")


class InstructionResponse(BaseModel):
    """Advisor指令响应"""
    instruction: str = Field(..., description="指令编码")
    reasoning: str = Field(..., description="推理说明")
    control_params: Dict = Field(..., description="控制参数")
    instructor_prompt: str = Field(..., description="给Instructor的提示")


class ModeCheckResponse(BaseModel):
    """模式检查响应"""
    user_id: int
    current_mode: str = Field(..., description="当前教学模式")
    mode_description: str = Field(..., description="模式说明")
    triggers: List[str] = Field(..., description="触发条件")


class RecommendationRequest(BaseModel):
    """推荐请求"""
    user_id: int
    question: Dict = Field(default_factory=dict, description="题目信息")
    user_state: UserStateRequest


class RecommendationResponse(BaseModel):
    """推荐响应"""
    user_id: int
    recommendation_reason: str = Field(..., description="推荐理由")
    tone_type: str = Field(..., description="语气类型")
    tone_example: str = Field(..., description="语气示例")


class TriggerCheckRequest(BaseModel):
    """触发条件检查请求"""
    user_id: int
    trigger_type: str = Field(..., description="触发类型: active/passive/scheduled")


class TriggerCheckResponse(BaseModel):
    """触发条件检查响应"""
    user_id: int
    trigger_type: str
    should_trigger: bool
    preprocessing_action: str


# ============ API端点 ============

@router.post("/instruction", response_model=InstructionResponse, 
             summary="生成Advisor指令")
async def generate_instruction(request: UserStateRequest):
    """
    根据用户学习状态生成Advisor控制指令
    
    会根据以下硬指标判断教学模式：
    - MODE_SCAFFOLD: P(L) < 0.4 或 连续2题错误
    - MODE_CHALLENGE: P(L) > 0.8 且 近期正确率高
    - MODE_ENCOURAGE: 连续3题错误或表达挫败感
    """
    try:
        advisor = get_advisor_agent()
        
        # 构建用户状态
        state = UserLearningState(
            user_id=request.user_id,
            theta=request.theta,
            p_known=request.p_known,
            consecutive_correct=request.consecutive_correct,
            consecutive_wrong=request.consecutive_wrong,
            recent_accuracy=request.recent_accuracy,
            weak_knowledge_points=request.weak_knowledge_points,
            recent_sentiment=request.recent_sentiment
        )
        
        # 生成指令
        instruction = advisor.generate_instruction(state)
        
        return InstructionResponse(**instruction.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode/check", response_model=ModeCheckResponse,
             summary="检查当前教学模式")
async def check_current_mode(request: UserStateRequest):
    """
    检查当前应该使用的教学模式
    
    返回当前模式及触发原因
    """
    try:
        advisor = get_advisor_agent()
        
        state = UserLearningState(
            user_id=request.user_id,
            theta=request.theta,
            p_known=request.p_known,
            consecutive_correct=request.consecutive_correct,
            consecutive_wrong=request.consecutive_wrong,
            recent_accuracy=request.recent_accuracy,
            weak_knowledge_points=request.weak_knowledge_points,
            recent_sentiment=request.recent_sentiment
        )
        
        mode = advisor.determine_mode(state)
        
        # 模式说明
        mode_descriptions = {
            "MODE_SCAFFOLD": "脚手架模式 - 分步引导，详细讲解",
            "MODE_CHALLENGE": "挑战模式 - 自主推导，最小提示",
            "MODE_ENCOURAGE": "鼓励模式 - 情感支持，正向强化",
            "MODE_NORMAL": "正常模式 - 标准教学流程"
        }
        
        # 触发条件
        triggers = []
        if state.p_known < 0.4:
            triggers.append(f"掌握度较低({state.p_known:.2f} < 0.4)")
        if state.consecutive_wrong >= 2:
            triggers.append(f"连续错误{state.consecutive_wrong}题")
        if state.consecutive_wrong >= 3:
            triggers.append(f"连续错误{state.consecutive_wrong}题(鼓励)")
        if state.p_known > 0.8 and state.recent_accuracy > 0.7:
            triggers.append(f"掌握度高({state.p_known:.2f})且正确率高({state.recent_accuracy:.2f})")
        if not triggers:
            triggers.append("默认模式")
        
        return ModeCheckResponse(
            user_id=request.user_id,
            current_mode=mode.value,
            mode_description=mode_descriptions.get(mode.value, "未知模式"),
            triggers=triggers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendation/reason", response_model=RecommendationResponse,
             summary="生成推荐理由")
async def generate_recommendation_reason(request: RecommendationRequest):
    """
    生成题目推荐理由
    
    使用PRD 3.5.1节模板：
    "根据你的学习记录，你在【{weak_kp}】方面还需要加强。
    这道题难度为{difficulty}，正好匹配你当前的能力水平。
    建议用时{estimated_time}分钟，完成后我会为你详细讲解。"
    """
    try:
        advisor = get_advisor_agent()
        
        state = UserLearningState(
            user_id=request.user_id,
            weak_knowledge_points=request.user_state.weak_knowledge_points
        )
        
        # 生成推荐理由
        reason = advisor.generate_recommendation_reason(
            request.question, 
            state
        )
        
        # 判断推荐类型并调整语气
        question_difficulty = request.question.get("difficulty", "medium")
        user_theta = request.user_state.theta
        
        # 简单判断推荐类型
        if question_difficulty == "hard" and user_theta < 0:
            rec_type = "downgrade"
        elif question_difficulty == "easy" and user_theta > 0.5:
            rec_type = "upgrade"
        else:
            rec_type = "same_level"
        
        tone_type, tone_example = advisor.adjust_tone(rec_type)
        
        return RecommendationResponse(
            user_id=request.user_id,
            recommendation_reason=reason,
            tone_type=tone_type,
            tone_example=tone_example
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/check", response_model=TriggerCheckResponse,
             summary="检查触发条件")
async def check_trigger(request: TriggerCheckRequest):
    """
    检查Advisor触发条件
    
    触发类型：
    - active: 主动请求（学生点击"推荐题目"）
    - passive: 被动触发（当前题目完成后自动触发）
    - scheduled: 定时触发（每日学习提醒）
    """
    try:
        trigger_actions = {
            "active": {
                "should_trigger": True,
                "action": "读取完整画像，执行完整推荐流程"
            },
            "passive": {
                "should_trigger": True,
                "action": "快速读取Redis缓存，执行轻量推荐"
            },
            "scheduled": {
                "should_trigger": True,
                "action": "基于历史数据生成日计划"
            }
        }
        
        action = trigger_actions.get(request.trigger_type, {
            "should_trigger": False,
            "action": "未知触发类型"
        })
        
        return TriggerCheckResponse(
            user_id=request.user_id,
            trigger_type=request.trigger_type,
            should_trigger=action["should_trigger"],
            preprocessing_action=action["action"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modes", summary="获取所有教学模式")
async def get_all_modes():
    """获取所有支持的教学模式及其说明"""
    return {
        "modes": [
            {
                "code": "MODE_SCAFFOLD",
                "name": "脚手架模式",
                "trigger_condition": "P(L) < 0.4 或 连续2题错误",
                "control_params": {
                    "hint_level": "detailed",
                    "step_by_step": True,
                    "allow_skip": True
                },
                "instructor_behavior": "必须分步讲解，每步后确认理解，允许随时请求提示"
            },
            {
                "code": "MODE_CHALLENGE",
                "name": "挑战模式",
                "trigger_condition": "P(L) > 0.8 且 近期正确率高",
                "control_params": {
                    "hint_level": "minimal",
                    "step_by_step": False,
                    "allow_skip": False
                },
                "instructor_behavior": "仅给出方向性提示，要求学生自主推导，不展开中间步骤"
            },
            {
                "code": "MODE_ENCOURAGE",
                "name": "鼓励模式",
                "trigger_condition": "连续3题错误或主动表达挫败感",
                "control_params": {
                    "hint_level": "adaptive",
                    "step_by_step": True,
                    "encouragement": True
                },
                "instructor_behavior": "先给予情感支持，再逐步引导，强调'错误是学习机会'"
            },
            {
                "code": "MODE_NORMAL",
                "name": "正常模式",
                "trigger_condition": "默认",
                "control_params": {
                    "hint_level": "standard",
                    "step_by_step": False,
                    "allow_skip": True
                },
                "instructor_behavior": "标准教学流程"
            }
        ]
    }


@router.post("/instruction/validate", summary="验证指令格式")
async def validate_instruction_format(instruction: Dict):
    """
    验证Advisor指令格式是否符合PRD规范
    
    检查字段：
    - instruction: 指令编码
    - reasoning: 推理说明
    - control_params: 控制参数
    - instructor_prompt: 给Instructor的提示
    """
    try:
        required_fields = ["instruction", "reasoning", "control_params", "instructor_prompt"]
        missing_fields = [f for f in required_fields if f not in instruction]
        
        # 检查指令编码是否有效
        valid_instructions = ["MODE_SCAFFOLD", "MODE_CHALLENGE", "MODE_ENCOURAGE", "MODE_NORMAL"]
        instruction_code = instruction.get("instruction", "")
        is_valid_code = instruction_code in valid_instructions
        
        return {
            "is_valid": len(missing_fields) == 0 and is_valid_code,
            "missing_fields": missing_fields,
            "invalid_instruction_code": not is_valid_code,
            "valid_codes": valid_instructions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Advisor服务健康检查")
async def advisor_health_check():
    """检查Advisor Agent服务状态"""
    try:
        advisor = get_advisor_agent()
        return {
            "status": "healthy",
            "service": "advisor-agent",
            "supported_modes": ["MODE_SCAFFOLD", "MODE_CHALLENGE", "MODE_ENCOURAGE", "MODE_NORMAL"],
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Advisor服务异常: {str(e)}")
