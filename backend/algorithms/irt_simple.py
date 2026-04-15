"""
简化版IRT (不依赖numpy/scipy)
用于快速测试和部署
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class QuestionParams:
    """题目参数"""
    difficulty: float  # b - 题目难度，范围[-3, +3]
    discrimination: float = 1.0  # a - 区分度，默认1.0
    
    def __post_init__(self):
        assert -3 <= self.difficulty <= 3, "难度必须在[-3, +3]之间"
        assert self.discrimination > 0, "区分度必须为正"


@dataclass
class IRTParams:
    theta_range: Tuple[float, float] = (-3.0, 3.0)

class IRTModel:
    """简化版IRT模型"""
    
    def __init__(self):
        self.params = IRTParams()
    
    def probability_correct(self, theta: float, question: QuestionParams) -> float:
        """计算答对概率"""
        a = question.discrimination
        b = question.difficulty
        exponent = -a * (theta - b)
        p_correct = 1.0 / (1.0 + math.exp(exponent))
        return p_correct
    
    def estimate_theta_simple(self, correct_count: int, total_count: int) -> float:
        """简化版theta估计"""
        if total_count == 0:
            return 0.0
        accuracy = correct_count / total_count
        theta = -3.0 + 6.0 * accuracy
        return max(-3.0, min(3.0, theta))
    
    def get_recommended_difficulty_range(self, theta: float, delta: float = 0.5):
        """获取推荐题目难度范围"""
        min_diff = max(-3.0, theta - delta)
        max_diff = min(3.0, theta + delta)
        return (min_diff, max_diff)


class KIRTModel:
    """K-IRT联合估算"""
    
    def __init__(self):
        self.irt = IRTModel()
    
    def compute_alpha(self, n_answers: int) -> float:
        """计算K-IRT权重"""
        return 0.8 if n_answers > 10 else 0.3
    
    def estimate_theta_final(self, theta_irt: float, theta_bkt: float, n_answers: int) -> float:
        """K-IRT联合估算"""
        alpha = self.compute_alpha(n_answers)
        theta_final = alpha * theta_irt + (1 - alpha) * theta_bkt
        return max(-3.0, min(3.0, theta_final))
    
    def bkt_mastery_to_theta(self, avg_mastery: float) -> float:
        """将BKT平均掌握度映射到theta范围"""
        theta = -3.0 + 6.0 * avg_mastery
        return max(-3.0, min(3.0, theta))


if __name__ == "__main__":
    print("=== Simple IRT Test ===")
    
    irt = IRTModel()
    question = QuestionParams(difficulty=0.0, discrimination=1.0)
    
    print("\nProbability correct:")
    for theta in [-3.0, 0.0, 3.0]:
        p = irt.probability_correct(theta, question)
        print(f"  theta={theta:+.1f} -> P(correct)={p:.4f}")
    
    print("\nRecommended difficulty range:")
    for theta in [-2.0, 0.0, 2.0]:
        min_d, max_d = irt.get_recommended_difficulty_range(theta)
        print(f"  theta={theta:+.1f} -> [{min_d:+.1f}, {max_d:+.1f}]")
    
    print("\nK-IRT:")
    kirt = KIRTModel()
    for n in [5, 15]:
        alpha = kirt.compute_alpha(n)
        theta_final = kirt.estimate_theta_final(0.5, 0.2, n)
        print(f"  n={n}, alpha={alpha}, theta_final={theta_final:.2f}")
