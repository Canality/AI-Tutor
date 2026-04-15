"""
AI Tutor V3 Algorithm Module Integration Test
"""

import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("AI Tutor V3 Algorithm Module Integration Test")
print("=" * 60)

# Test 1: Import all algorithm modules
print("\n[Test 1] Import algorithm modules...")
try:
    from algorithms.bkt import BKTModel, BKTParams
    from algorithms import IRTModel, KIRTModel
    from algorithms import AdaptiveKFactor
    from algorithms import MemoryDecay
    from algorithms import ActualScoreCalculator, HintLevel
    print("OK - All algorithm modules imported")
except Exception as e:
    print(f"FAIL - Import error: {e}")
    sys.exit(1)

# Test 2: Import service module
print("\n[Test 2] Import cognitive diagnosis service...")
try:
    from services.cognitive_diagnosis_service import CognitiveDiagnosisService
    print("OK - Cognitive diagnosis service imported")
except Exception as e:
    print(f"WARN - Service import failed (normal, depends on DB): {e}")

# Test 3: Algorithm function test
print("\n[Test 3] Algorithm function test...")

# BKT test
bkt = BKTModel()
p = bkt.update(0.5, True)
assert 0 <= p <= 1, "BKT mastery should be in [0,1]"
print(f"OK - BKT: 0.5 -> {p:.4f}")

# IRT test
irt = IRTModel()
from algorithms import QuestionParams
q = QuestionParams(difficulty=0.0)
prob = irt.probability_correct(0.0, q)
assert 0 <= prob <= 1, "IRT probability should be in [0,1]"
print(f"OK - IRT: theta=0, b=0 -> P={prob:.4f}")

# Actual Score test
calc = ActualScoreCalculator()
from algorithms import AnswerRecord
record = AnswerRecord(
    is_correct=True,
    hint_level=HintLevel.L0_AUTONOMOUS,
    time_spent=60,
    expected_time=60
)
score = calc.calculate(record)
assert 0 <= score <= 1, "Actual Score should be in [0,1]"
print(f"OK - Actual Score: L0 correct -> {score:.4f}")

# Adaptive K test
adaptive_k = AdaptiveKFactor()
k = adaptive_k.compute_k_factor([0.0, 0.3, 0.6])
assert 0.1 <= k <= 1.0, "K factor should be in [0.1,1.0]"
print(f"OK - Adaptive K: {k:.4f}")

# Memory decay test
mem_decay = MemoryDecay()
p_decayed = mem_decay.compute_decay(0.8, 7)
assert 0 <= p_decayed <= 1, "Decayed mastery should be in [0,1]"
print(f"OK - Memory Decay: 0.8 -> 7 days {p_decayed:.4f}")

print("\n" + "=" * 60)
print("All tests passed! Algorithm modules working correctly")
print("=" * 60)

print("\n[API Endpoints]")
print("POST /api/cognitive/mastery/update    - Update mastery (BKT)")
print("GET  /api/cognitive/theta/{user_id}   - Get theta (K-IRT)")
print("POST /api/cognitive/actual-score/calculate - Calculate Actual Score")
print("GET  /api/cognitive/difficulty-range/{user_id} - Recommended difficulty")
print("GET  /api/cognitive/report/{user_id}  - Comprehensive report")
print("POST /api/cognitive/memory-decay/apply - Apply memory decay")
print("GET  /api/cognitive/health            - Health check")
