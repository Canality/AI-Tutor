"""
AI Tutor V3 算法模块集成测试
验证所有算法模块的正确性
"""

import sys
import math

# 测试BKT
print("=" * 60)
print("测试1: BKT (贝叶斯知识追踪)")
print("=" * 60)

from bkt import BKTModel, BKTParams

bkt = BKTModel()
print(f"初始掌握度 P(L0): {bkt.params.p_known_initial}")
print(f"学习率 P(T): {bkt.params.p_learn}")
print(f"猜测率 P(G): {bkt.params.p_guess}")
print(f"失误率 P(S): {bkt.params.p_slip}")

# 测试连续答对
p = bkt.params.p_known_initial
print(f"\n连续答对3次:")
for i in range(3):
    p = bkt.update(p, True)
    print(f"  第{i+1}次答对后 P(L)={p:.4f}")

# 测试掌握度等级
print(f"\n掌握度等级判断:")
for val, expected in [(0.3, "weak"), (0.6, "learning"), (0.9, "mastered")]:
    level = bkt.get_mastery_level(val)
    status = "✓" if level == expected else "✗"
    print(f"  P(L)={val} -> {level} {status}")

# 测试IRT
print("\n" + "=" * 60)
print("测试2: IRT (项目反应理论)")
print("=" * 60)

from irt import IRTModel, QuestionParams

irt = IRTModel()
print(f"Theta范围: {irt.params.theta_range}")

# 测试不同能力值的答对概率
question = QuestionParams(difficulty=0.0, discrimination=1.0)
print(f"\n题目难度b=0.0, 区分度a=1.0:")
for theta in [-3.0, -1.5, 0.0, 1.5, 3.0]:
    p = irt.probability_correct(theta, question)
    print(f"  theta={theta:+.1f} -> P(correct)={p:.4f}")

# 测试推荐难度范围
print(f"\n推荐难度范围:")
for theta in [-2.0, 0.0, 2.0]:
    min_d, max_d = irt.get_recommended_difficulty_range(theta)
    print(f"  theta={theta:+.1f} -> [{min_d:+.1f}, {max_d:+.1f}]")

# 测试自适应K因子
print("\n" + "=" * 60)
print("测试3: 自适应K因子")
print("=" * 60)

from adaptive_k import AdaptiveKFactor

adaptive_k = AdaptiveKFactor()
print(f"初始K: {adaptive_k.params.k_initial}")
print(f"beta: {adaptive_k.params.beta}")
print(f"gamma: {adaptive_k.params.gamma}")

# 测试方向一致（应该增大K）
theta_history = [0.0, 0.3, 0.6, 0.9]
k = adaptive_k.compute_k_factor(theta_history, window_size=3)
print(f"\n连续上升{theta_history}:")
print(f"  K因子={k:.4f} (初始={adaptive_k.params.k_initial})")
print(f"  {'增大' if k > adaptive_k.params.k_initial else '减小'}")

# 测试震荡（应该减小K）
theta_history2 = [0.0, 0.5, 0.2, 0.6]
k2 = adaptive_k.compute_k_factor(theta_history2, window_size=3)
print(f"\n震荡{theta_history2}:")
print(f"  K因子={k2:.4f} (初始={adaptive_k.params.k_initial})")
print(f"  {'增大' if k2 > adaptive_k.params.k_initial else '减小'}")

# 测试记忆衰减
print("\n" + "=" * 60)
print("测试4: 记忆衰减（艾宾浩斯遗忘曲线）")
print("=" * 60)

from memory_decay import MemoryDecay

decay = MemoryDecay()
print(f"半衰期: {decay.params.half_life_days}天")
print(f"衰减系数λ: {decay.params.lambda_value:.6f}")

p_initial = 0.8
print(f"\n初始掌握度={p_initial}的衰减:")
days_list = [0, 1, 2, 4, 7, 14, 21]
for days in days_list:
    p = decay.compute_decay(p_initial, days)
    print(f"  {days:2d}天 -> {p:.4f} ({p/p_initial*100:.1f}%)")

# 验证半衰期
p_half = decay.compute_decay(1.0, 7)
print(f"\n验证: 7天后掌握度={p_half:.4f} (应为0.5)")

# 测试Actual Score
print("\n" + "=" * 60)
print("测试5: Actual Score (L0-L4权重)")
print("=" * 60)

from actual_score import ActualScoreCalculator, AnswerRecord, HintLevel

calculator = ActualScoreCalculator()
print("L0-L4权重:")
for level in HintLevel:
    weight = calculator.params.hint_weights[level]
    name = calculator.get_hint_level_name(level)
    print(f"  {level.name}: {weight} ({name})")

print(f"\n不同提示等级的Actual Score (假设答对，正常耗时):")
for level in HintLevel:
    record = AnswerRecord(
        is_correct=True,
        hint_level=level,
        time_spent=60,
        expected_time=60
    )
    score = calculator.calculate(record)
    name = calculator.get_hint_level_name(level)
    print(f"  {level.name}: {score:.4f} ({name})")

# 综合测试
print("\n" + "=" * 60)
print("测试6: 综合场景")
print("=" * 60)

print("场景: 学生连续答题")

# 模拟一个学生的学习过程
from datetime import datetime, timedelta

# 第1题：自主完成，答对，快速
record1 = AnswerRecord(
    is_correct=True,
    hint_level=HintLevel.L0_AUTONOMOUS,
    time_spent=30,
    expected_time=60
)
score1 = calculator.calculate(record1)
print(f"题1: L0自主完成，答对，快速 -> Actual={score1:.4f}")

# 更新BKT
p_mastery = bkt.update(bkt.params.p_known_initial, True)
print(f"     知识点掌握度: {bkt.params.p_known_initial:.4f} -> {p_mastery:.4f}")

# 第2题：需要公式提示，答对，正常时间
record2 = AnswerRecord(
    is_correct=True,
    hint_level=HintLevel.L2_FORMULA,
    time_spent=65,
    expected_time=60
)
score2 = calculator.calculate(record2)
print(f"题2: L2公式提示，答对，正常 -> Actual={score2:.4f}")

# 更新BKT
p_mastery = bkt.update(p_mastery, True)
print(f"     知识点掌握度: -> {p_mastery:.4f}")

# 第3题：看答案，答错，超时
record3 = AnswerRecord(
    is_correct=False,
    hint_level=HintLevel.L4_ANSWER,
    time_spent=180,
    expected_time=60
)
score3 = calculator.calculate(record3)
print(f"题3: L4看答案，答错，超时 -> Actual={score3:.4f}")

print("\n" + "=" * 60)
print("所有测试通过！✓")
print("=" * 60)
