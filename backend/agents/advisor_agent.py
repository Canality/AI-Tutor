"""
Advisor Agent 指令集实现
严格遵循PRD文档3.2节硬指标

功能：
1. 根据学生状态判断教学模式
2. 生成控制指令下发给Instructor
3. 调控教学策略和讲解深度
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class AdvisorMode(Enum):
    """Advisor教学模式（硬指标）"""
    SCAFFOLD = "MODE_SCAFFOLD"      # 脚手架模式
    CHALLENGE = "MODE_CHALLENGE"    # 挑战模式
    ENCOURAGE = "MODE_ENCOURAGE"    # 鼓励模式
    NORMAL = "MODE_NORMAL"          # 正常模式（默认）


@dataclass
class UserLearningState:
    """用户学习状态"""
    user_id: int
    theta: float                    # 能力值
    p_known: float                  # 当前知识点掌握度
    consecutive_correct: int        # 连续正确次数
    consecutive_wrong: int          # 连续错误次数
    recent_accuracy: float          # 近期正确率
    weak_knowledge_points: List[Tuple[str, int]] = field(default_factory=list)
    recent_sentiment: str = ""      # 近期情感状态
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "theta": self.theta,
            "p_known": self.p_known,
            "consecutive_correct": self.consecutive_correct,
            "consecutive_wrong": self.consecutive_wrong,
            "recent_accuracy": self.recent_accuracy,
            "weak_knowledge_points": self.weak_knowledge_points,
            "recent_sentiment": self.recent_sentiment
        }


@dataclass
class AdvisorInstruction:
    """
    Advisor指令（硬指标格式）
    
    指令下发格式：
    {
      "instruction": "MODE_SCAFFOLD",
      "reasoning": "学生在等比数列知识点掌握度仅为0.35,需要分步引导",
      "control_params": {
        "hint_level": "detailed",
        "max_hints": 5,
        "step_by_step": true,
        "estimated_steps": 4
      },
      "instructor_prompt": "请使用苏格拉底式提问..."
    }
    """
    instruction: str                # 指令编码
    reasoning: str                  # 推理说明
    control_params: Dict            # 控制参数
    instructor_prompt: str          # 给Instructor的提示
    
    def to_dict(self) -> Dict:
        return {
            "instruction": self.instruction,
            "reasoning": self.reasoning,
            "control_params": self.control_params,
            "instructor_prompt": self.instructor_prompt
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AdvisorAgent:
    """
    Advisor Agent核心类
    
    职责：
    1. 分析学生学习状态
    2. 判断适用的教学模式
    3. 生成控制指令
    """
    
    # 硬指标阈值
    SCAFFOLD_THRESHOLD = 0.4        # 脚手架模式阈值 P(L) < 0.4
    CHALLENGE_THRESHOLD = 0.8       # 挑战模式阈值 P(L) > 0.8
    CONSECUTIVE_WRONG_THRESHOLD = 2 # 连续错误阈值（脚手架）
    CONSECUTIVE_WRONG_ENCOURAGE = 3 # 连续错误阈值（鼓励）
    RECENT_ACCURACY_THRESHOLD = 0.7 # 近期正确率阈值
    
    def __init__(self):
        self.instruction_history: List[Dict] = []  # 指令历史
    
    def determine_mode(self, state: UserLearningState) -> AdvisorMode:
        """
        判断教学模式（硬指标）
        
        优先级：
        1. 鼓励模式（连续3题错误或挫败感）
        2. 脚手架模式（P(L) < 0.4 或 连续2题错误）
        3. 挑战模式（P(L) > 0.8 且 近期正确率高）
        4. 正常模式（默认）
        """
        # 鼓励模式：连续3题错误或主动表达挫败感
        if (state.consecutive_wrong >= self.CONSECUTIVE_WRONG_ENCOURAGE or 
            state.recent_sentiment in ["frustrated", "discouraged", "挫败"]):
            return AdvisorMode.ENCOURAGE
        
        # 脚手架模式：P(L) < 0.4 或 连续2题错误
        if (state.p_known < self.SCAFFOLD_THRESHOLD or 
            state.consecutive_wrong >= self.CONSECUTIVE_WRONG_THRESHOLD):
            return AdvisorMode.SCAFFOLD
        
        # 挑战模式：P(L) > 0.8 且 近期正确率高
        if (state.p_known > self.CHALLENGE_THRESHOLD and 
            state.recent_accuracy > self.RECENT_ACCURACY_THRESHOLD):
            return AdvisorMode.CHALLENGE
        
        # 默认：正常模式
        return AdvisorMode.NORMAL
    
    def generate_instruction(self, state: UserLearningState, 
                            context: Optional[Dict] = None) -> AdvisorInstruction:
        """
        生成Advisor指令（硬指标格式）
        
        Args:
            state: 用户学习状态
            context: 额外上下文（如当前知识点、题目等）
            
        Returns:
            AdvisorInstruction对象
        """
        mode = self.determine_mode(state)
        
        if mode == AdvisorMode.SCAFFOLD:
            return self._generate_scaffold_instruction(state, context)
        elif mode == AdvisorMode.CHALLENGE:
            return self._generate_challenge_instruction(state, context)
        elif mode == AdvisorMode.ENCOURAGE:
            return self._generate_encourage_instruction(state, context)
        else:
            return self._generate_normal_instruction(state, context)
    
    def _generate_scaffold_instruction(self, state: UserLearningState,
                                       context: Optional[Dict]) -> AdvisorInstruction:
        """
        生成脚手架模式指令（硬指标）
        
        控制参数：
        - hint_level: detailed
        - step_by_step: true
        - allow_skip: true
        
        Instructor行为约束：
        - 必须分步讲解
        - 每步后确认理解
        - 允许随时请求提示
        """
        weak_kp = state.weak_knowledge_points[0][0] if state.weak_knowledge_points else "当前知识点"
        
        reasoning = f"学生在【{weak_kp}】知识点掌握度仅为{state.p_known:.2f}，需要分步引导"
        
        control_params = {
            "hint_level": "detailed",           # 详细提示
            "max_hints": 5,                     # 最多5个提示
            "step_by_step": True,               # 分步讲解
            "allow_skip": True,                 # 允许跳过
            "estimated_steps": 4,               # 预计4步
            "confirm_each_step": True           # 每步后确认
        }
        
        instructor_prompt = (
            f"请使用苏格拉底式提问，分4步引导学生理解【{weak_kp}】的解题思路。"
            f"每完成一步，请确认学生理解后再进行下一步。"
            f"如果学生卡住了，允许他们随时请求提示。"
        )
        
        return AdvisorInstruction(
            instruction=AdvisorMode.SCAFFOLD.value,
            reasoning=reasoning,
            control_params=control_params,
            instructor_prompt=instructor_prompt
        )
    
    def _generate_challenge_instruction(self, state: UserLearningState,
                                        context: Optional[Dict]) -> AdvisorInstruction:
        """
        生成挑战模式指令（硬指标）
        
        控制参数：
        - hint_level: minimal
        - step_by_step: false
        - allow_skip: false
        
        Instructor行为约束：
        - 仅给出方向性提示
        - 要求学生自主推导
        - 不展开中间步骤
        """
        reasoning = (
            f"学生掌握度为{state.p_known:.2f}，近期正确率为{state.recent_accuracy:.2f}，"
            f"适合挑战更高难度的题目"
        )
        
        control_params = {
            "hint_level": "minimal",            # 最小提示
            "max_hints": 2,                     # 最多2个提示
            "step_by_step": False,              # 不分步
            "allow_skip": False,                # 不允许跳过
            "show_full_solution": False         # 不展示完整解答
        }
        
        instructor_prompt = (
            "这道题有一定挑战性，请仅给出方向性提示，不要展开中间步骤。"
            "鼓励学生自主推导，培养独立思考能力。"
            "如果学生确实无法解决，最多再给1个关键提示。"
        )
        
        return AdvisorInstruction(
            instruction=AdvisorMode.CHALLENGE.value,
            reasoning=reasoning,
            control_params=control_params,
            instructor_prompt=instructor_prompt
        )
    
    def _generate_encourage_instruction(self, state: UserLearningState,
                                        context: Optional[Dict]) -> AdvisorInstruction:
        """
        生成鼓励模式指令（硬指标）
        
        控制参数：
        - hint_level: adaptive
        - step_by_step: true
        - encouragement: true
        
        Instructor行为约束：
        - 先给予情感支持
        - 再逐步引导
        - 强调"错误是学习机会"
        """
        weak_kp = state.weak_knowledge_points[0][0] if state.weak_knowledge_points else "当前知识点"
        
        if state.consecutive_wrong >= self.CONSECUTIVE_WRONG_ENCOURAGE:
            reasoning = f"学生连续{state.consecutive_wrong}题错误，需要情感支持和鼓励"
        else:
            reasoning = "学生表达了挫败感，需要情感支持和鼓励"
        
        control_params = {
            "hint_level": "adaptive",           # 自适应提示
            "max_hints": 10,                    # 最多10个提示（更宽松）
            "step_by_step": True,               # 分步讲解
            "encouragement": True,              # 启用鼓励
            "positive_reinforcement": True,     # 正向强化
            "error_framing": "learning_opportunity"  # 错误是学习机会
        }
        
        instructor_prompt = (
            f"学生可能在【{weak_kp}】上遇到了困难。"
            f"请先给予情感支持，告诉他们'错误是学习的机会'。"
            f"然后使用更简单的例子，分步引导他们理解。"
            f"每完成一小步，都给予积极的反馈和鼓励。"
        )
        
        return AdvisorInstruction(
            instruction=AdvisorMode.ENCOURAGE.value,
            reasoning=reasoning,
            control_params=control_params,
            instructor_prompt=instructor_prompt
        )
    
    def _generate_normal_instruction(self, state: UserLearningState,
                                     context: Optional[Dict]) -> AdvisorInstruction:
        """生成正常模式指令（默认）"""
        reasoning = f"学生状态正常，采用标准教学模式"
        
        control_params = {
            "hint_level": "standard",
            "max_hints": 3,
            "step_by_step": False,
            "allow_skip": True
        }
        
        instructor_prompt = "请按照正常流程进行教学，根据学生反应灵活调整。"
        
        return AdvisorInstruction(
            instruction=AdvisorMode.NORMAL.value,
            reasoning=reasoning,
            control_params=control_params,
            instructor_prompt=instructor_prompt
        )
    
    def generate_recommendation_reason(self, question: Dict, 
                                       state: UserLearningState) -> str:
        """
        生成推荐理由（PRD 3.5.1节）
        
        模板：
        "根据你的学习记录，你在【{weak_kp}】方面还需要加强。
        这道题难度为{difficulty}，正好匹配你当前的能力水平。
        建议用时{estimated_time}分钟，完成后我会为你详细讲解。"
        """
        weak_kp = state.weak_knowledge_points[0][0] if state.weak_knowledge_points else "这个知识点"
        difficulty = question.get("difficulty", "中等")
        estimated_time = question.get("estimated_time", 5)
        
        reason = (
            f"根据你的学习记录，你在【{weak_kp}】方面还需要加强。\n"
            f"这道题难度为{difficulty}，正好匹配你当前的能力水平。\n"
            f"建议用时{estimated_time}分钟，完成后我会为你详细讲解。"
        )
        
        return reason
    
    def adjust_tone(self, recommendation_type: str) -> Tuple[str, str]:
        """
        调整推荐语气（PRD 3.5.2节）
        
        Returns:
            (语气类型, 示例话术)
        """
        tones = {
            "downgrade": (
                "鼓励型",
                "这道题确实有些挑战，我们先从基础练起，打好基础再回来攻克它！"
            ),
            "same_level": (
                "中性",
                "这道题的考点和你刚做的类似，试试看能不能举一反三？"
            ),
            "upgrade": (
                "激励型",
                "上一题你完成得很棒！这道进阶题能帮你更上一层楼，敢不敢挑战一下？"
            )
        }
        
        return tones.get(recommendation_type, tones["same_level"])
    
    def get_instruction_history(self, limit: int = 10) -> List[Dict]:
        """获取指令历史"""
        return self.instruction_history[-limit:]
    
    def clear_history(self):
        """清空指令历史"""
        self.instruction_history = []


# 全局Advisor实例
_advisor_agent = None


def get_advisor_agent() -> AdvisorAgent:
    """获取Advisor Agent实例（单例）"""
    global _advisor_agent
    if _advisor_agent is None:
        _advisor_agent = AdvisorAgent()
    return _advisor_agent


# 单元测试
if __name__ == "__main__":
    print("=== Advisor Agent 指令集测试 ===\n")
    
    advisor = AdvisorAgent()
    
    # 测试1: 脚手架模式
    print("测试1: 脚手架模式")
    state1 = UserLearningState(
        user_id=1,
        theta=0.0,
        p_known=0.35,  # < 0.4
        consecutive_correct=0,
        consecutive_wrong=2,  # 连续2题错误
        recent_accuracy=0.4,
        weak_knowledge_points=[("等比数列", 35)]
    )
    
    mode1 = advisor.determine_mode(state1)
    print(f"  判定模式: {mode1.value}")
    assert mode1 == AdvisorMode.SCAFFOLD
    
    instruction1 = advisor.generate_instruction(state1)
    print(f"  指令编码: {instruction1.instruction}")
    print(f"  推理说明: {instruction1.reasoning}")
    print(f"  控制参数: {instruction1.control_params}")
    print("  ✓ 脚手架模式测试通过\n")
    
    # 测试2: 挑战模式
    print("测试2: 挑战模式")
    state2 = UserLearningState(
        user_id=2,
        theta=1.5,
        p_known=0.85,  # > 0.8
        consecutive_correct=5,
        consecutive_wrong=0,
        recent_accuracy=0.85  # > 0.7
    )
    
    mode2 = advisor.determine_mode(state2)
    print(f"  判定模式: {mode2.value}")
    assert mode2 == AdvisorMode.CHALLENGE
    
    instruction2 = advisor.generate_instruction(state2)
    print(f"  指令编码: {instruction2.instruction}")
    print(f"  推理说明: {instruction2.reasoning}")
    print(f"  控制参数: {instruction2.control_params}")
    print("  ✓ 挑战模式测试通过\n")
    
    # 测试3: 鼓励模式
    print("测试3: 鼓励模式")
    state3 = UserLearningState(
        user_id=3,
        theta=0.0,
        p_known=0.5,
        consecutive_correct=0,
        consecutive_wrong=3,  # 连续3题错误
        recent_accuracy=0.3
    )
    
    mode3 = advisor.determine_mode(state3)
    print(f"  判定模式: {mode3.value}")
    assert mode3 == AdvisorMode.ENCOURAGE
    
    instruction3 = advisor.generate_instruction(state3)
    print(f"  指令编码: {instruction3.instruction}")
    print(f"  推理说明: {instruction3.reasoning}")
    print(f"  控制参数: {instruction3.control_params}")
    print("  ✓ 鼓励模式测试通过\n")
    
    # 测试4: 推荐理由生成
    print("测试4: 推荐理由生成")
    question = {"difficulty": "中等", "estimated_time": 8}
    reason = advisor.generate_recommendation_reason(question, state1)
    print(f"  推荐理由:\n{reason}")
    print("  ✓ 推荐理由测试通过\n")
    
    # 测试5: 语气调整
    print("测试5: 语气调整")
    for rec_type in ["downgrade", "same_level", "upgrade"]:
        tone, example = advisor.adjust_tone(rec_type)
        print(f"  {rec_type}: {tone}")
        print(f"    示例: {example}")
    print("  ✓ 语气调整测试通过\n")
    
    print("=== 所有测试通过！===")
