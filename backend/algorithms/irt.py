"""
IRT (Item Response Theory) 项目反应理论算法
严格遵循PRD文档：theta范围[-3, +3]，题目难度b范围[-3, +3]，区分度a默认1.0
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize_scalar


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
    """IRT全局参数"""
    theta_range: Tuple[float, float] = (-3.0, 3.0)  # 能力值范围
    
    def clamp_theta(self, theta: float) -> float:
        """将能力值限制在范围内"""
        return max(self.theta_range[0], min(self.theta_range[1], theta))


class IRTModel:
    """
    IRT模型 - 评估学生能力值theta
    
    核心公式（双参数逻辑斯蒂模型）：
    P(correct|theta, a, b) = 1 / (1 + exp(-a * (theta - b)))
    
    其中：
    - theta: 学生能力值，范围[-3, +3]
    - a: 题目区分度，默认1.0
    - b: 题目难度，范围[-3, +3]
    """
    
    def __init__(self, params: Optional[IRTParams] = None):
        self.params = params or IRTParams()
    
    def probability_correct(self, theta: float, question: QuestionParams) -> float:
        """
        计算答对概率
        
        Args:
            theta: 学生能力值
            question: 题目参数
            
        Returns:
            答对概率
        """
        a = question.discrimination
        b = question.difficulty
        
        # P(correct) = 1 / (1 + exp(-a * (theta - b)))
        exponent = -a * (theta - b)
        p_correct = 1.0 / (1.0 + math.exp(exponent))
        
        return p_correct
    
    def likelihood(self, theta: float, 
                   questions: List[QuestionParams], 
                   responses: List[bool]) -> float:
        """
        计算似然函数 L(theta | responses)
        
        Args:
            theta: 能力值
            questions: 题目列表
            responses: 答题结果列表
            
        Returns:
            似然值
        """
        likelihood = 1.0
        
        for question, response in zip(questions, responses):
            p = self.probability_correct(theta, question)
            if response:  # 答对
                likelihood *= p
            else:  # 答错
                likelihood *= (1 - p)
        
        return likelihood
    
    def log_likelihood(self, theta: float,
                       questions: List[QuestionParams],
                       responses: List[bool]) -> float:
        """
        计算对数似然函数（数值稳定性更好）
        """
        log_likelihood = 0.0
        
        for question, response in zip(questions, responses):
            p = self.probability_correct(theta, question)
            # 防止log(0)
            p = max(1e-10, min(1 - 1e-10, p))
            
            if response:  # 答对
                log_likelihood += math.log(p)
            else:  # 答错
                log_likelihood += math.log(1 - p)
        
        return log_likelihood
    
    def estimate_theta(self, 
                       questions: List[QuestionParams],
                       responses: List[bool],
                       method: str = "mle") -> float:
        """
        估计学生能力值theta
        
        Args:
            questions: 题目列表
            responses: 答题结果列表
            method: 估计方法，"mle"（最大似然估计）
            
        Returns:
            估计的能力值theta
        """
        if len(questions) == 0:
            return 0.0  # 默认中等能力
        
        if method == "mle":
            return self._estimate_theta_mle(questions, responses)
        else:
            raise ValueError(f"不支持的估计方法: {method}")
    
    def _estimate_theta_mle(self, 
                            questions: List[QuestionParams],
                            responses: List[bool]) -> float:
        """
        使用最大似然估计(MLE)估计theta
        """
        # 定义负对数似然函数（要最小化）
        def neg_log_likelihood(theta):
            return -self.log_likelihood(theta, questions, responses)
        
        # 在theta范围内进行优化
        result = minimize_scalar(
            neg_log_likelihood,
            bounds=self.params.theta_range,
            method='bounded'
        )
        
        estimated_theta = result.x
        return self.params.clamp_theta(estimated_theta)
    
    def estimate_theta_simple(self, 
                              correct_count: int, 
                              total_count: int) -> float:
        """
        简化版theta估计（基于正确率）
        
        将正确率线性映射到[-3, +3]范围
        """
        if total_count == 0:
            return 0.0
        
        accuracy = correct_count / total_count
        # 映射到[-3, +3]
        theta = -3.0 + 6.0 * accuracy
        return self.params.clamp_theta(theta)
    
    def get_recommended_difficulty_range(self, theta: float, 
                                         delta: float = 0.5) -> Tuple[float, float]:
        """
        获取推荐题目难度范围
        
        PRD标准：基础区间 [theta - 0.5, theta + 0.5]
        
        Args:
            theta: 学生能力值
            delta: 难度偏移量，默认0.5
            
        Returns:
            (min_difficulty, max_difficulty)
        """
        min_diff = max(-3.0, theta - delta)
        max_diff = min(3.0, theta + delta)
        return (min_diff, max_diff)
    
    def select_next_question(self, 
                            theta: float,
                            available_questions: List[QuestionParams],
                            seen_questions: set = None) -> Optional[QuestionParams]:
        """
        选择下一道最合适的题目
        
        策略：选择难度最接近theta且未做过的题目
        """
        if seen_questions is None:
            seen_questions = set()
        
        best_question = None
        best_diff = float('inf')
        
        for question in available_questions:
            # 跳过已做过的题目
            if question in seen_questions:
                continue
            
            # 计算难度差异
            diff = abs(question.difficulty - theta)
            if diff < best_diff:
                best_diff = diff
                best_question = question
        
        return best_question


class KIRTModel:
    """
    K-IRT联合估算模型
    
    PRD公式：theta_final = α * theta_irt + (1-α) * theta_bkt
    
    权重分配（硬指标）：
    - 答题记录充足 (n > 10)：α = 0.8（主要依赖IRT）
    - 答题记录稀疏 (n <= 10)：α = 0.3（主要依赖BKT先验）
    """
    
    def __init__(self, irt_model: Optional[IRTModel] = None):
        self.irt = irt_model or IRTModel()
    
    def compute_alpha(self, n_answers: int) -> float:
        """
        计算K-IRT权重α
        
        Args:
            n_answers: 答题记录数量
            
        Returns:
            α值
        """
        if n_answers > 10:
            return 0.8  # 主要依赖IRT
        else:
            return 0.3  # 主要依赖BKT先验
    
    def estimate_theta_final(self,
                            theta_irt: float,
                            theta_bkt: float,
                            n_answers: int) -> float:
        """
        K-IRT联合估算
        
        Args:
            theta_irt: IRT估计的能力值
            theta_bkt: BKT估计的能力值（从掌握度映射）
            n_answers: 答题记录数量
            
        Returns:
            最终能力值theta
        """
        alpha = self.compute_alpha(n_answers)
        theta_final = alpha * theta_irt + (1 - alpha) * theta_bkt
        return self.irt.params.clamp_theta(theta_final)
    
    def bkt_mastery_to_theta(self, avg_mastery: float) -> float:
        """
        将BKT平均掌握度映射到theta范围
        
        映射公式：theta = -3 + 6 * avg_mastery
        """
        theta = -3.0 + 6.0 * avg_mastery
        return self.irt.params.clamp_theta(theta)


# 单元测试
if __name__ == "__main__":
    print("=== IRT算法测试 ===\n")
    
    # 测试1：概率计算
    print("测试1：不同能力值的答对概率")
    irt = IRTModel()
    question = QuestionParams(difficulty=0.0, discrimination=1.0)
    
    for theta in [-3.0, -1.5, 0.0, 1.5, 3.0]:
        p = irt.probability_correct(theta, question)
        print(f"theta={theta:+.1f}, P(correct)={p:.4f}")
    
    # 测试2：theta估计
    print("\n测试2：MLE估计theta")
    questions = [
        QuestionParams(difficulty=-1.0),
        QuestionParams(difficulty=0.0),
        QuestionParams(difficulty=1.0),
    ]
    responses = [True, True, False]  # 对-对-错
    
    theta_est = irt.estimate_theta(questions, responses)
    print(f"答题结果: 对-对-错")
    print(f"估计的theta: {theta_est:.4f}")
    
    # 测试3：推荐难度范围
    print("\n测试3：推荐难度范围")
    for theta in [-2.0, 0.0, 2.0]:
        min_diff, max_diff = irt.get_recommended_difficulty_range(theta)
        print(f"theta={theta:+.1f} -> 推荐难度范围[{min_diff:+.1f}, {max_diff:+.1f}]")
    
    # 测试4：K-IRT联合估算
    print("\n测试4：K-IRT联合估算")
    kirt = KIRTModel(irt)
    
    for n in [5, 15]:  # 稀疏 vs 充足
        alpha = kirt.compute_alpha(n)
        theta_irt = 0.5
        theta_bkt = 0.2
        theta_final = kirt.estimate_theta_final(theta_irt, theta_bkt, n)
        print(f"n={n:2d}, α={alpha:.1f}, theta_irt={theta_irt:+.2f}, "
              f"theta_bkt={theta_bkt:+.2f}, theta_final={theta_final:+.2f}")
