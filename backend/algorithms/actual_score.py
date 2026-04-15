"""
Actual Score 实际得分计算器
严格遵循PRD文档：L0-L4权重 1.0/0.8/0.6/0.4/0.1
"""

from typing import Optional, Dict
from dataclasses import dataclass
from enum import IntEnum


class HintLevel(IntEnum):
    """提示等级 - 严格遵循PRD文档"""
    L0_AUTONOMOUS = 0   # 自主完成
    L1_DIRECTION = 1    # 方向提示
    L2_FORMULA = 2      # 公式提示
    L3_STEP = 3         # 步骤推导
    L4_ANSWER = 4       # 完整答案


@dataclass
class ActualScoreParams:
    """Actual Score权重参数 - 硬指标"""
    # L0-L4权重（来自PRD文档）
    hint_weights: Dict[HintLevel, float] = None
    
    # 子分数权重（来自PRD文档）
    w_correct: float = 0.6      # 正确性权重
    w_hint: float = 0.25        # 提示使用权重
    w_time: float = 0.1         # 时间效率权重
    w_skip: float = 0.05        # 跳过行为权重
    
    # 时间奖惩阈值
    time_fast_threshold: float = 0.5   # 快速完成阈值（<50%期望时间）
    time_slow_threshold: float = 2.0   # 超时阈值（>200%期望时间）
    time_bonus: float = 0.05           # 快速奖励
    time_penalty: float = -0.05        # 超时惩罚
    
    def __post_init__(self):
        if self.hint_weights is None:
            # PRD标准权重
            self.hint_weights = {
                HintLevel.L0_AUTONOMOUS: 1.0,
                HintLevel.L1_DIRECTION: 0.8,
                HintLevel.L2_FORMULA: 0.6,
                HintLevel.L3_STEP: 0.4,
                HintLevel.L4_ANSWER: 0.1,
            }
        
        # 验证权重和为1
        total_weight = self.w_correct + self.w_hint + self.w_time + self.w_skip
        assert abs(total_weight - 1.0) < 1e-6, f"权重和必须等于1，当前为{total_weight}"


@dataclass
class AnswerRecord:
    """答题记录"""
    is_correct: bool                    # 是否正确
    hint_level: HintLevel              # 提示等级
    time_spent: float                   # 实际耗时（秒）
    expected_time: float                # 期望耗时（秒）
    skip_reason: Optional[str] = None  # 跳过原因
    
    @property
    def is_skipped(self) -> bool:
        """是否跳过"""
        return self.skip_reason is not None


class ActualScoreCalculator:
    """
    Actual Score 实际得分计算器
    
    PRD公式：
    Actual Score = w_correct * S_correct + w_hint * S_hint + 
                   w_time * S_time + w_skip * S_skip
    
    其中：
    - S_correct: 0或1（答对/答错）
    - S_hint: 1 - HintPenalty，HintPenalty根据L0-L4确定
    - S_time: 时间奖惩
    - S_skip: 跳过调整
    """
    
    def __init__(self, params: Optional[ActualScoreParams] = None):
        self.params = params or ActualScoreParams()
    
    def calculate(self, record: AnswerRecord) -> float:
        """
        计算Actual Score
        
        Args:
            record: 答题记录
            
        Returns:
            Actual Score (0-1之间)
        """
        # 1. 正确性分数
        s_correct = 1.0 if record.is_correct else 0.0
        
        # 2. 提示分数（基于L0-L4权重）
        s_hint = self._calculate_hint_score(record.hint_level)
        
        # 3. 时间分数
        s_time = self._calculate_time_score(record.time_spent, record.expected_time)
        
        # 4. 跳过分数
        s_skip = self._calculate_skip_score(record.skip_reason)
        
        # 加权求和
        actual_score = (
            self.params.w_correct * s_correct +
            self.params.w_hint * s_hint +
            self.params.w_time * s_time +
            self.params.w_skip * s_skip
        )
        
        # 限制在[0,1]范围内
        return max(0.0, min(1.0, actual_score))
    
    def _calculate_hint_score(self, hint_level: HintLevel) -> float:
        """
        计算提示分数
        
        直接使用L0-L4权重
        """
        return self.params.hint_weights.get(hint_level, 0.5)
    
    def _calculate_time_score(self, 
                             time_spent: float, 
                             expected_time: float) -> float:
        """
        计算时间分数
        
        PRD标准：
        - 实际耗时 < 期望耗时50%：+0.05（快速奖励）
        - 实际耗时 > 期望耗时200%：-0.05（超时惩罚）
        - 其他：0
        """
        if expected_time <= 0:
            return 0.0
        
        ratio = time_spent / expected_time
        
        if ratio < self.params.time_fast_threshold:
            return self.params.time_bonus  # +0.05
        elif ratio > self.params.time_slow_threshold:
            return self.params.time_penalty  # -0.05
        else:
            return 0.0
    
    def _calculate_skip_score(self, skip_reason: Optional[str]) -> float:
        """
        计算跳过分数
        
        PRD标准：
        - 跳过原因"太简单"：+0.1
        - 跳过原因"太难了"：-0.1
        - 未跳过：0
        """
        if skip_reason is None:
            return 0.0
        
        skip_reason_lower = skip_reason.lower()
        
        if "简单" in skip_reason_lower or "easy" in skip_reason_lower:
            return 0.1
        elif "难" in skip_reason_lower or "hard" in skip_reason_lower or "difficult" in skip_reason_lower:
            return -0.1
        else:
            return 0.0
    
    def calculate_simple(self,
                        is_correct: bool,
                        hint_level: HintLevel) -> float:
        """
        简化版计算（仅考虑正确性和提示等级）
        
        用于快速评估
        """
        weight_correct = self.params.w_correct
        weight_hint = self.params.w_hint
        
        s_correct = 1.0 if is_correct else 0.0
        s_hint = self._calculate_hint_score(hint_level)
        
        # 重新归一化权重
        total_weight = weight_correct + weight_hint
        w_c = weight_correct / total_weight
        w_h = weight_hint / total_weight
        
        return w_c * s_correct + w_h * s_hint
    
    def get_hint_level_name(self, hint_level: HintLevel) -> str:
        """获取提示等级名称"""
        names = {
            HintLevel.L0_AUTONOMOUS: "自主完成",
            HintLevel.L1_DIRECTION: "方向提示",
            HintLevel.L2_FORMULA: "公式提示",
            HintLevel.L3_STEP: "步骤推导",
            HintLevel.L4_ANSWER: "完整答案",
        }
        return names.get(hint_level, "未知")
    
    def get_hint_level_description(self, hint_level: HintLevel) -> str:
        """获取提示等级描述（用于LLM Prompt）"""
        descriptions = {
            HintLevel.L0_AUTONOMOUS: "学生独立完成，不提供任何提示",
            HintLevel.L1_DIRECTION: "提供解题方向、方法名称或苏格拉底式反问",
            HintLevel.L2_FORMULA: "提供特定的公式、定理，或指出题干中的隐含条件",
            HintLevel.L3_STEP: "代入题目具体数值，推导并输出第一步或最核心的计算步骤",
            HintLevel.L4_ANSWER: "给出包含所有中间推导的完整答案",
        }
        return descriptions.get(hint_level, "")


# 单元测试
if __name__ == "__main__":
    print("=== Actual Score计算器测试 ===\n")
    
    # 测试1：参数验证
    print("测试1：默认参数")
    calculator = ActualScoreCalculator()
    print(f"正确性权重: {calculator.params.w_correct}")
    print(f"提示权重: {calculator.params.w_hint}")
    print(f"时间权重: {calculator.params.w_time}")
    print(f"跳过权重: {calculator.params.w_skip}")
    print("L0-L4权重:")
    for level, weight in calculator.params.hint_weights.items():
        print(f"  {level.name}: {weight}")
    
    # 测试2：不同提示等级的分数
    print("\n测试2：不同提示等级的Actual Score（假设答对，正常耗时）")
    for level in HintLevel:
        record = AnswerRecord(
            is_correct=True,
            hint_level=level,
            time_spent=60,
            expected_time=60
        )
        score = calculator.calculate(record)
        print(f"{level.name}: {score:.4f} ({calculator.get_hint_level_name(level)})")
    
    # 测试3：答错的情况
    print("\n测试3：答错的情况（L2提示）")
    record_wrong = AnswerRecord(
        is_correct=False,
        hint_level=HintLevel.L2_FORMULA,
        time_spent=120,
        expected_time=60
    )
    score_wrong = calculator.calculate(record_wrong)
    print(f"答错 + L2提示 + 超时: {score_wrong:.4f}")
    
    # 测试4：时间奖惩
    print("\n测试4：时间奖惩")
    base_record = AnswerRecord(
        is_correct=True,
        hint_level=HintLevel.L0_AUTONOMOUS,
        time_spent=60,
        expected_time=60
    )
    
    # 快速完成
    record_fast = AnswerRecord(
        is_correct=True,
        hint_level=HintLevel.L0_AUTONOMOUS,
        time_spent=20,  # < 50%期望时间
        expected_time=60
    )
    
    # 超时
    record_slow = AnswerRecord(
        is_correct=True,
        hint_level=HintLevel.L0_AUTONOMOUS,
        time_spent=150,  # > 200%期望时间
        expected_time=60
    )
    
    print(f"正常耗时: {calculator.calculate(base_record):.4f}")
    print(f"快速完成: {calculator.calculate(record_fast):.4f} (+{calculator.params.time_bonus})")
    print(f"超时完成: {calculator.calculate(record_slow):.4f} ({calculator.params.time_penalty})")
    
    # 测试5：跳过
    print("\n测试5：跳过题目")
    record_skip_easy = AnswerRecord(
        is_correct=False,
        hint_level=HintLevel.L0_AUTONOMOUS,
        time_spent=0,
        expected_time=60,
        skip_reason="太简单"
    )
    record_skip_hard = AnswerRecord(
        is_correct=False,
        hint_level=HintLevel.L0_AUTONOMOUS,
        time_spent=0,
        expected_time=60,
        skip_reason="太难了"
    )
    
    print(f"跳过-太简单: {calculator.calculate(record_skip_easy):.4f}")
    print(f"跳过-太难了: {calculator.calculate(record_skip_hard):.4f}")
    
    # 测试6：综合案例
    print("\n测试6：综合案例")
    scenarios = [
        ("学霸", True, HintLevel.L0_AUTONOMOUS, 30, 60, None),
        ("普通学生", True, HintLevel.L2_FORMULA, 70, 60, None),
        ("学困生", False, HintLevel.L4_ANSWER, 180, 60, None),
        ("粗心", False, HintLevel.L0_AUTONOMOUS, 40, 60, None),
    ]
    
    for name, correct, hint, time_spent, expected, skip in scenarios:
        record = AnswerRecord(
            is_correct=correct,
            hint_level=hint,
            time_spent=time_spent,
            expected_time=expected,
            skip_reason=skip
        )
        score = calculator.calculate(record)
        print(f"{name}: {score:.4f}")
