"""
自适应K因子优化器
严格遵循PRD文档：beta=0.1, gamma=0.5, K_initial=0.3
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class AdaptiveKParams:
    """自适应K因子参数 - 硬指标"""
    k_initial: float = 0.3   # 初始K值
    beta: float = 0.1        # 调整幅度系数
    gamma: float = 0.5       # 非线性压缩因子
    k_min: float = 0.1       # K值下限
    k_max: float = 1.0       # K值上限
    
    def __post_init__(self):
        """验证参数"""
        assert 0 < self.k_initial <= 1, "K_initial必须在(0,1]之间"
        assert 0 < self.beta <= 1, "beta必须在(0,1]之间"
        assert 0 < self.gamma <= 1, "gamma必须在(0,1]之间"


class AdaptiveKFactor:
    """
    自适应K因子优化器
    
    模拟机器学习自适应学习率，动态调整学生画像的收敛速度
    
    核心逻辑：
    1. 若连续误差方向一致 -> 增大K因子（加速追赶）
    2. 若误差正负震荡 -> 减小K因子（进入稳定期）
    
    PRD公式：K_adaptive = K_initial + β * (|θ_new - θ_old| / (1 + γ))
    """
    
    def __init__(self, params: Optional[AdaptiveKParams] = None):
        self.params = params or AdaptiveKParams()
    
    def compute_k_factor(self, 
                        theta_history: List[float],
                        window_size: int = 3) -> float:
        """
        计算自适应K因子
        
        Args:
            theta_history: theta历史值列表
            window_size: 判断震荡的窗口大小，默认3
            
        Returns:
            自适应K因子
        """
        k_initial = self.params.k_initial
        beta = self.params.beta
        gamma = self.params.gamma
        
        # 历史记录不足，使用初始值
        if len(theta_history) < 2:
            return k_initial
        
        # 计算最近的误差（变化量）
        errors = [theta_history[i] - theta_history[i-1] 
                  for i in range(1, len(theta_history))]
        
        # 如果历史记录少于窗口大小，使用全部
        recent_errors = errors[-window_size:] if len(errors) >= window_size else errors
        
        # 判断误差方向
        is_consistent = all(e > 0 for e in recent_errors) or all(e < 0 for e in recent_errors)
        
        # 计算最近误差的大小
        recent_error_magnitude = abs(recent_errors[-1])
        
        if is_consistent:
            # 方向一致：增大K因子（加速追赶）
            adjustment = beta * recent_error_magnitude / (1 + gamma)
            k_new = k_initial + adjustment
        else:
            # 震荡：减小K因子（进入稳定期）
            adjustment = beta * recent_error_magnitude / (1 + gamma)
            k_new = k_initial - adjustment
        
        # 限制在合理范围内
        return max(self.params.k_min, min(self.params.k_max, k_new))
    
    def compute_k_factor_simple(self, 
                               theta_old: float,
                               theta_new: float,
                               consecutive_same_direction: int = 0) -> float:
        """
        简化版K因子计算（基于单次更新）
        
        Args:
            theta_old: 旧theta值
            theta_new: 新theta值
            consecutive_same_direction: 连续同方向次数
            
        Returns:
            自适应K因子
        """
        k_initial = self.params.k_initial
        beta = self.params.beta
        gamma = self.params.gamma
        
        # 计算误差大小
        error_magnitude = abs(theta_new - theta_old)
        
        # 根据连续同方向次数调整
        if consecutive_same_direction > 0:
            # 方向一致：增大K
            multiplier = 1 + 0.1 * consecutive_same_direction
            adjustment = beta * error_magnitude * multiplier / (1 + gamma)
            k_new = k_initial + adjustment
        else:
            # 震荡或首次：使用初始值或略减小
            adjustment = beta * error_magnitude / (1 + gamma)
            k_new = k_initial - adjustment
        
        return max(self.params.k_min, min(self.params.k_max, k_new))
    
    def update_theta_with_k(self,
                           theta_old: float,
                           target_theta: float,
                           k_factor: Optional[float] = None) -> float:
        """
        使用自适应K因子更新theta
        
        Args:
            theta_old: 当前theta值
            target_theta: 目标theta值（算法估计值）
            k_factor: K因子，如果为None则使用初始值
            
        Returns:
            更新后的theta值
        """
        if k_factor is None:
            k_factor = self.params.k_initial
        
        # 向目标值移动，步长由K因子控制
        theta_new = theta_old + k_factor * (target_theta - theta_old)
        
        return theta_new
    
    def should_increase_k(self, 
                         errors: List[float],
                         window_size: int = 3) -> bool:
        """
        判断是否应该增大K因子
        
        条件：最近window_size个误差方向一致
        
        Args:
            errors: 误差历史列表
            window_size: 窗口大小
            
        Returns:
            是否应该增大K
        """
        if len(errors) < window_size:
            return False
        
        recent_errors = errors[-window_size:]
        return all(e > 0 for e in recent_errors) or all(e < 0 for e in recent_errors)
    
    def should_decrease_k(self,
                         errors: List[float],
                         window_size: int = 3) -> bool:
        """
        判断是否应该减小K因子
        
        条件：最近window_size个误差方向不一致（震荡）
        """
        if len(errors) < window_size:
            return False
        
        recent_errors = errors[-window_size:]
        has_positive = any(e > 0 for e in recent_errors)
        has_negative = any(e < 0 for e in recent_errors)
        return has_positive and has_negative


# 单元测试
if __name__ == "__main__":
    print("=== 自适应K因子优化器测试 ===\n")
    
    # 测试1：参数验证
    print("测试1：默认参数")
    adaptive_k = AdaptiveKFactor()
    print(f"K_initial={adaptive_k.params.k_initial}")
    print(f"beta={adaptive_k.params.beta}")
    print(f"gamma={adaptive_k.params.gamma}")
    
    # 测试2：方向一致（应该增大K）
    print("\n测试2：连续3次同方向误差（增大K）")
    theta_history = [0.0, 0.3, 0.6, 0.9]  # 持续上升
    k = adaptive_k.compute_k_factor(theta_history, window_size=3)
    print(f"theta历史: {theta_history}")
    print(f"计算K因子: {k:.4f} (初始={adaptive_k.params.k_initial})")
    print(f"K变化: {'增大' if k > adaptive_k.params.k_initial else '减小'}")
    
    # 测试3：震荡（应该减小K）
    print("\n测试3：震荡误差（减小K）")
    theta_history2 = [0.0, 0.5, 0.2, 0.6, 0.3]  # 上下震荡
    k2 = adaptive_k.compute_k_factor(theta_history2, window_size=3)
    print(f"theta历史: {theta_history2}")
    print(f"计算K因子: {k2:.4f} (初始={adaptive_k.params.k_initial})")
    print(f"K变化: {'增大' if k2 > adaptive_k.params.k_initial else '减小'}")
    
    # 测试4：theta更新
    print("\n测试4：使用K因子更新theta")
    theta_old = 0.5
    target_theta = 1.2
    k_factor = 0.4
    theta_new = adaptive_k.update_theta_with_k(theta_old, target_theta, k_factor)
    print(f"旧theta: {theta_old}")
    print(f"目标theta: {target_theta}")
    print(f"K因子: {k_factor}")
    print(f"新theta: {theta_new:.4f}")
    
    # 测试5：不同连续次数
    print("\n测试5：不同连续同方向次数的影响")
    theta_old = 0.0
    theta_new = 0.5
    for consecutive in [0, 1, 2, 3]:
        k = adaptive_k.compute_k_factor_simple(theta_old, theta_new, consecutive)
        print(f"连续{consecutive}次同方向 -> K={k:.4f}")
