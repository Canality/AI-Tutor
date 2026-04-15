"""
BKT (Bayesian Knowledge Tracing) 贝叶斯知识追踪算法
严格遵循PRD文档参数：P(T)=0.3, P(G)=0.2, P(S)=0.1, P(L0)=0.5
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class BKTParams:
    """BKT算法参数 - 硬指标"""
    p_learn: float = 0.3      # P(T) - 学习率
    p_guess: float = 0.2      # P(G) - 猜测率
    p_slip: float = 0.1       # P(S) - 失误率
    p_known_initial: float = 0.5  # P(L0) - 初始掌握度
    
    def __post_init__(self):
        """验证参数范围"""
        assert 0 <= self.p_learn <= 1, "P(T)必须在[0,1]之间"
        assert 0 <= self.p_guess <= 1, "P(G)必须在[0,1]之间"
        assert 0 <= self.p_slip <= 1, "P(S)必须在[0,1]之间"
        assert 0 <= self.p_known_initial <= 1, "P(L0)必须在[0,1]之间"


class BKTModel:
    """
    BKT模型 - 追踪学生对单一知识点的掌握概率
    
    核心公式：
    1. P(Correct) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)
    2. P(L|Correct) = P(L) * (1 - P(S)) / P(Correct)
    3. P(L|Wrong) = P(L) * P(S) / P(Wrong)
    4. P(L_new) = P(L|observation) + (1 - P(L|observation)) * P(T)
    """
    
    def __init__(self, params: Optional[BKTParams] = None):
        self.params = params or BKTParams()
    
    def update(self, p_known: float, is_correct: bool) -> float:
        """
        根据答题结果更新掌握度
        
        Args:
            p_known: 当前掌握度 P(L)
            is_correct: 是否答对
            
        Returns:
            更新后的掌握度 P(L_new)
        """
        p_learn = self.params.p_learn
        p_guess = self.params.p_guess
        p_slip = self.params.p_slip
        
        # 步骤1：计算答对/答错的概率
        if is_correct:
            # P(Correct) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)
            p_correct = p_known * (1 - p_slip) + (1 - p_known) * p_guess
            # 步骤2：贝叶斯更新 P(L|Correct)
            p_known_given_obs = p_known * (1 - p_slip) / p_correct
        else:
            # P(Wrong) = P(L) * P(S) + (1 - P(L)) * (1 - P(G))
            p_wrong = p_known * p_slip + (1 - p_known) * (1 - p_guess)
            # 步骤2：贝叶斯更新 P(L|Wrong)
            p_known_given_obs = p_known * p_slip / p_wrong
        
        # 步骤3：学习转移 P(L_new) = P(L|obs) + (1 - P(L|obs)) * P(T)
        p_known_new = p_known_given_obs + (1 - p_known_given_obs) * p_learn
        
        # 限制在[0,1]范围内
        return max(0.0, min(1.0, p_known_new))
    
    def predict_correct_probability(self, p_known: float) -> float:
        """
        预测答对概率
        
        Args:
            p_known: 当前掌握度
            
        Returns:
            答对概率
        """
        p_guess = self.params.p_guess
        p_slip = self.params.p_slip
        
        # P(Correct) = P(L) * (1 - P(S)) + (1 - P(L)) * P(G)
        p_correct = p_known * (1 - p_slip) + (1 - p_known) * p_guess
        return p_correct
    
    def update_sequence(self, answers: List[bool]) -> List[float]:
        """
        根据答题序列更新掌握度
        
        Args:
            answers: 答题结果列表，True表示答对，False表示答错
            
        Returns:
            每次答题后的掌握度列表
        """
        p_known = self.params.p_known_initial
        mastery_history = [p_known]
        
        for is_correct in answers:
            p_known = self.update(p_known, is_correct)
            mastery_history.append(p_known)
        
        return mastery_history
    
    def get_mastery_level(self, p_known: float) -> str:
        """
        根据掌握度获取等级（用于知识树颜色显示）
        
        PRD标准：
        - 绿色：P(L) >= 0.8（已掌握）
        - 黄色：0.5 <= P(L) < 0.8（学习中）
        - 红色：P(L) < 0.5（薄弱点）
        """
        if p_known >= 0.8:
            return "mastered"  # 绿色
        elif p_known >= 0.5:
            return "learning"  # 黄色
        else:
            return "weak"      # 红色


def batch_update_bkt(
    user_answers: Dict[int, List[bool]],
    params: Optional[BKTParams] = None
) -> Dict[int, float]:
    """
    批量更新多个知识点的掌握度
    
    Args:
        user_answers: {knowledge_point_id: [answers]}
        params: BKT参数
        
    Returns:
        {knowledge_point_id: final_mastery}
    """
    model = BKTModel(params)
    results = {}
    
    for kp_id, answers in user_answers.items():
        if not answers:
            results[kp_id] = model.params.p_known_initial
        else:
            mastery_history = model.update_sequence(answers)
            results[kp_id] = mastery_history[-1]
    
    return results


# 单元测试
if __name__ == "__main__":
    # 测试用例1：连续答对
    print("=== 测试1：连续答对3次 ===")
    model = BKTModel()
    p = model.params.p_known_initial
    print(f"初始掌握度: {p:.4f}")
    
    for i in range(3):
        p = model.update(p, True)
        print(f"第{i+1}次答对后: {p:.4f}")
    
    # 测试用例2：连续答错
    print("\n=== 测试2：连续答错2次 ===")
    model2 = BKTModel()
    p = model2.params.p_known_initial
    print(f"初始掌握度: {p:.4f}")
    
    for i in range(2):
        p = model2.update(p, False)
        print(f"第{i+1}次答错后: {p:.4f}")
    
    # 测试用例3：混合答题
    print("\n=== 测试3：对-错-对-对 ===")
    model3 = BKTModel()
    answers = [True, False, True, True]
    history = model3.update_sequence(answers)
    print("掌握度变化:", [f"{h:.4f}" for h in history])
    
    # 测试用例4：掌握度等级
    print("\n=== 测试4：掌握度等级 ===")
    test_values = [0.3, 0.6, 0.9]
    for v in test_values:
        level = model.get_mastery_level(v)
        print(f"P(L)={v:.2f} -> {level}")
