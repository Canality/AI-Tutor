"""
AI Tutor V3 认知诊断算法模块
包含：BKT、IRT、K-IRT、自适应K因子、记忆衰减、Actual Score等算法

严格遵循PRD文档参数：
- BKT: P(T)=0.3, P(G)=0.2, P(S)=0.1, P(L0)=0.5
- IRT: theta范围[-3, +3], 题目难度b范围[-3, +3], 区分度a默认1.0
- K-IRT: n>10时α=0.8, n<=10时α=0.3
- 自适应K因子: β=0.1, γ=0.5, K_initial=0.3
- 记忆衰减: 半衰期7天, λ=ln(2)/7
- Actual Score: L0-L4权重 1.0/0.8/0.6/0.4/0.1
"""

from .bkt import BKTModel, BKTParams, batch_update_bkt
from .irt_simple import IRTModel, IRTParams, QuestionParams, KIRTModel
from .adaptive_k import AdaptiveKFactor, AdaptiveKParams
from .memory_decay import MemoryDecay, MemoryDecayParams
from .actual_score import (
    ActualScoreCalculator, 
    ActualScoreParams, 
    AnswerRecord, 
    HintLevel
)

__all__ = [
    # BKT
    'BKTModel',
    'BKTParams',
    'batch_update_bkt',
    
    # IRT
    'IRTModel',
    'IRTParams',
    'QuestionParams',
    'KIRTModel',
    
    # 自适应K因子
    'AdaptiveKFactor',
    'AdaptiveKParams',
    
    # 记忆衰减
    'MemoryDecay',
    'MemoryDecayParams',
    
    # Actual Score
    'ActualScoreCalculator',
    'ActualScoreParams',
    'AnswerRecord',
    'HintLevel',
]

__version__ = '3.0.0'
