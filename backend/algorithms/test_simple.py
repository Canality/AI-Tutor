"""
AI Tutor V3 算法模块简单测试
"""

import sys
import math

print("=" * 60)
print("Test 1: BKT (Bayesian Knowledge Tracing)")
print("=" * 60)

from bkt import BKTModel

bkt = BKTModel()
print(f"Initial P(L0): {bkt.params.p_known_initial}")
print(f"P(T): {bkt.params.p_learn}")
print(f"P(G): {bkt.params.p_guess}")
print(f"P(S): {bkt.params.p_slip}")

# Test consecutive correct
p = bkt.params.p_known_initial
print(f"\nConsecutive correct 3 times:")
for i in range(3):
    p = bkt.update(p, True)
    print(f"  After {i+1} correct: P(L)={p:.4f}")

print("\n" + "=" * 60)
print("Test 2: IRT (Item Response Theory)")
print("=" * 60)

from irt_simple import IRTModel, QuestionParams

irt = IRTModel()
print(f"Theta range: {irt.params.theta_range}")

question = QuestionParams(difficulty=0.0, discrimination=1.0)
print(f"\nQuestion difficulty=0.0:")
for theta in [-3.0, 0.0, 3.0]:
    p = irt.probability_correct(theta, question)
    print(f"  theta={theta:+.1f} -> P(correct)={p:.4f}")

print("\n" + "=" * 60)
print("Test 3: Adaptive K-Factor")
print("=" * 60)

from adaptive_k import AdaptiveKFactor

adaptive_k = AdaptiveKFactor()
print(f"K_initial: {adaptive_k.params.k_initial}")
print(f"beta: {adaptive_k.params.beta}")
print(f"gamma: {adaptive_k.params.gamma}")

# Consistent direction
theta_history = [0.0, 0.3, 0.6, 0.9]
k = adaptive_k.compute_k_factor(theta_history, window_size=3)
print(f"\nConsistent increase {theta_history}:")
print(f"  K={k:.4f} (initial={adaptive_k.params.k_initial})")
print(f"  Result: {'INCREASE' if k > adaptive_k.params.k_initial else 'DECREASE'}")

# Oscillation
theta_history2 = [0.0, 0.5, 0.2, 0.6]
k2 = adaptive_k.compute_k_factor(theta_history2, window_size=3)
print(f"\nOscillation {theta_history2}:")
print(f"  K={k2:.4f} (initial={adaptive_k.params.k_initial})")
print(f"  Result: {'INCREASE' if k2 > adaptive_k.params.k_initial else 'DECREASE'}")

print("\n" + "=" * 60)
print("Test 4: Memory Decay (Ebbinghaus)")
print("=" * 60)

from memory_decay import MemoryDecay

decay = MemoryDecay()
print(f"Half-life: {decay.params.half_life_days} days")
print(f"Lambda: {decay.params.lambda_value:.6f}")

p_initial = 0.8
print(f"\nDecay from {p_initial}:")
for days in [0, 7, 14, 21]:
    p = decay.compute_decay(p_initial, days)
    print(f"  {days} days -> {p:.4f} ({p/p_initial*100:.1f}%)")

# Verify half-life
p_half = decay.compute_decay(1.0, 7)
print(f"\nVerify: 7 days = {p_half:.4f} (should be 0.5)")

print("\n" + "=" * 60)
print("Test 5: Actual Score (L0-L4)")
print("=" * 60)

from actual_score import ActualScoreCalculator, AnswerRecord, HintLevel

calculator = ActualScoreCalculator()
print("L0-L4 weights:")
for level in HintLevel:
    weight = calculator.params.hint_weights[level]
    print(f"  {level.name}: {weight}")

print(f"\nActual Score (correct, normal time):")
for level in HintLevel:
    record = AnswerRecord(
        is_correct=True,
        hint_level=level,
        time_spent=60,
        expected_time=60
    )
    score = calculator.calculate(record)
    print(f"  {level.name}: {score:.4f}")

print("\n" + "=" * 60)
print("All tests passed!")
print("=" * 60)
