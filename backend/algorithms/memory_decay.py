"""
记忆衰减模型（艾宾浩斯遗忘曲线）
严格遵循PRD文档：半衰期参数 lambda = ln(2) / 7（默认7天半衰期）
"""

import math
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class MemoryDecayParams:
    """记忆衰减参数 - 硬指标"""
    half_life_days: float = 7.0  # 半衰期（天）
    
    def __post_init__(self):
        """计算衰减系数 lambda = ln(2) / half_life"""
        self.lambda_param = math.log(2) / self.half_life_days
    
    @property
    def lambda_value(self) -> float:
        """获取衰减系数"""
        return self.lambda_param


class MemoryDecay:
    """
    记忆衰减模型
    
    模拟记忆半衰期，计算长时间未练习的知识点掌握度的自然衰减
    
    PRD公式：P(L)_new = P(L) * e^(-λ * Δt)
    其中：λ = ln(2) / 7（7天半衰期）
    
    衰减规律：
    - 7天后：掌握度减半（50%）
    - 14天后：掌握度为25%
    - 21天后：掌握度为12.5%
    """
    
    def __init__(self, params: Optional[MemoryDecayParams] = None):
        self.params = params or MemoryDecayParams()
    
    def compute_decay(self, 
                     p_known: float,
                     days_passed: float) -> float:
        """
        计算衰减后的掌握度
        
        Args:
            p_known: 当前掌握度
            days_passed: 经过的天数
            
        Returns:
            衰减后的掌握度
        """
        if days_passed <= 0:
            return p_known
        
        # 衰减公式：P(L)_new = P(L) * e^(-λ * Δt)
        decay_factor = math.exp(-self.params.lambda_value * days_passed)
        p_known_new = p_known * decay_factor
        
        # 限制最小值（防止完全遗忘）
        return max(0.01, p_known_new)
    
    def compute_decay_with_timestamp(self,
                                     p_known: float,
                                     last_practiced_at: datetime,
                                     now: Optional[datetime] = None) -> float:
        """
        基于时间戳计算衰减
        
        Args:
            p_known: 当前掌握度
            last_practiced_at: 最后练习时间
            now: 当前时间，默认为现在
            
        Returns:
            衰减后的掌握度
        """
        if now is None:
            now = datetime.now()
        
        # 计算经过的天数
        delta = now - last_practiced_at
        days_passed = delta.total_seconds() / (24 * 3600)
        
        return self.compute_decay(p_known, days_passed)
    
    def get_decay_schedule(self, 
                          p_known_initial: float,
                          days_list: list = None) -> dict:
        """
        获取衰减时间表
        
        Args:
            p_known_initial: 初始掌握度
            days_list: 要计算的天数列表，默认[0, 1, 2, 4, 7, 14, 21, 30]
            
        Returns:
            {天数: 掌握度}
        """
        if days_list is None:
            days_list = [0, 1, 2, 4, 7, 14, 21, 30]
        
        schedule = {}
        for days in days_list:
            p = self.compute_decay(p_known_initial, days)
            schedule[days] = p
        
        return schedule
    
    def should_review(self,
                     p_known: float,
                     last_practiced_at: datetime,
                     threshold: float = 0.5,
                     now: Optional[datetime] = None) -> bool:
        """
        判断是否需要复习
        
        条件：衰减后的掌握度低于阈值
        
        Args:
            p_known: 当前掌握度
            last_practiced_at: 最后练习时间
            threshold: 复习阈值，默认0.5
            now: 当前时间
            
        Returns:
            是否需要复习
        """
        p_decayed = self.compute_decay_with_timestamp(
            p_known, last_practiced_at, now
        )
        return p_decayed < threshold
    
    def estimate_next_review_time(self,
                                  p_known: float,
                                  last_practiced_at: datetime,
                                  target_mastery: float = 0.5) -> datetime:
        """
        估计下次需要复习的时间
        
        计算掌握度衰减到目标值所需的时间
        
        Args:
            p_known: 当前掌握度
            last_practiced_at: 最后练习时间
            target_mastery: 目标掌握度阈值，默认0.5
            
        Returns:
            预计的下次复习时间
        """
        if p_known <= target_mastery:
            # 已经低于阈值，立即复习
            return last_practiced_at
        
        # 解方程：target = p_known * e^(-λ * t)
        # t = -ln(target / p_known) / λ
        days_until_review = -math.log(target_mastery / p_known) / self.params.lambda_value
        
        next_review = last_practiced_at + timedelta(days=days_until_review)
        return next_review
    
    def batch_apply_decay(self,
                         mastery_data: list,
                         now: Optional[datetime] = None) -> list:
        """
        批量应用衰减
        
        Args:
            mastery_data: [{user_id, kp_id, p_known, last_practiced_at}, ...]
            now: 当前时间
            
        Returns:
            更新后的掌握度列表
        """
        if now is None:
            now = datetime.now()
        
        results = []
        for item in mastery_data:
            p_decayed = self.compute_decay_with_timestamp(
                item['p_known'],
                item['last_practiced_at'],
                now
            )
            results.append({
                'user_id': item['user_id'],
                'kp_id': item['kp_id'],
                'p_known_original': item['p_known'],
                'p_known_decayed': p_decayed,
                'days_passed': (now - item['last_practiced_at']).days
            })
        
        return results


# 单元测试
if __name__ == "__main__":
    print("=== 记忆衰减模型测试 ===\n")
    
    # 测试1：参数验证
    print("测试1：默认参数")
    decay = MemoryDecay()
    print(f"半衰期: {decay.params.half_life_days}天")
    print(f"衰减系数λ: {decay.params.lambda_value:.6f}")
    print(f"验证: ln(2)/7 = {math.log(2)/7:.6f}")
    
    # 测试2：衰减计算
    print("\n测试2：不同时间的衰减")
    p_initial = 0.8
    days_list = [0, 1, 2, 4, 7, 14, 21, 30]
    
    print(f"初始掌握度: {p_initial}")
    print("天数 -> 掌握度")
    for days in days_list:
        p = decay.compute_decay(p_initial, days)
        print(f"{days:2d}天 -> {p:.4f} ({p/p_initial*100:.1f}%)")
    
    # 测试3：半衰期验证
    print("\n测试3：半衰期验证")
    p_half = decay.compute_decay(1.0, 7)  # 7天后
    print(f"7天后掌握度: {p_half:.4f} (应为0.5)")
    
    # 测试4：是否需要复习
    print("\n测试4：是否需要复习")
    last_practice = datetime.now() - timedelta(days=10)
    should = decay.should_review(0.8, last_practice, threshold=0.5)
    print(f"10天前练习，掌握度0.8，是否需要复习: {should}")
    
    # 测试5：下次复习时间
    print("\n测试5：下次复习时间预测")
    last_practice = datetime.now()
    next_review = decay.estimate_next_review_time(0.8, last_practice, target_mastery=0.5)
    days_until = (next_review - last_practice).days
    print(f"当前掌握度0.8，预计{days_until}天后需要复习")
    print(f"下次复习时间: {next_review.strftime('%Y-%m-%d')}")
    
    # 测试6：批量衰减
    print("\n测试6：批量衰减")
    mock_data = [
        {'user_id': 1, 'kp_id': 101, 'p_known': 0.9, 'last_practiced_at': datetime.now() - timedelta(days=3)},
        {'user_id': 1, 'kp_id': 102, 'p_known': 0.7, 'last_practiced_at': datetime.now() - timedelta(days=10)},
        {'user_id': 1, 'kp_id': 103, 'p_known': 0.5, 'last_practiced_at': datetime.now() - timedelta(days=20)},
    ]
    
    results = decay.batch_apply_decay(mock_data)
    print("用户1的知识点掌握度衰减:")
    for r in results:
        print(f"  KP-{r['kp_id']}: {r['p_known_original']:.2f} -> {r['p_known_decayed']:.2f} "
              f"({r['days_passed']}天未练习)")
