"""
AI Tutor V3 Mock API Server
用于前端开发和演示，无需数据库依赖
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uvicorn

# 导入算法模块
from algorithms import (
    BKTModel, IRTModel, KIRTModel, QuestionParams,
    AdaptiveKFactor, MemoryDecay, ActualScoreCalculator,
    AnswerRecord, HintLevel
)

app = FastAPI(
    title="AI Tutor V3 Mock API",
    version="3.0.0",
    description="AI Tutor V3 认知诊断算法Mock服务"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Mock数据存储 ============

# 模拟用户数据
mock_users = {
    1: {
        "user_id": 1,
        "username": "student_001",
        "theta": 0.5,
        "total_questions": 50,
        "correct_count": 35,
        "avg_mastery": 0.65,
        "created_at": "2026-01-01"
    },
    2: {
        "user_id": 2,
        "username": "student_002", 
        "theta": -0.3,
        "total_questions": 20,
        "correct_count": 10,
        "avg_mastery": 0.45,
        "created_at": "2026-01-15"
    },
    3: {
        "user_id": 3,
        "username": "student_003",
        "theta": 1.2,
        "total_questions": 100,
        "correct_count": 85,
        "avg_mastery": 0.82,
        "created_at": "2025-12-01"
    }
}

# 模拟知识点掌握度
mock_mastery = {
    (1, 101): {"p_known": 0.8, "level": "mastered", "last_practiced": datetime.now() - timedelta(days=2)},
    (1, 102): {"p_known": 0.6, "level": "learning", "last_practiced": datetime.now() - timedelta(days=1)},
    (1, 103): {"p_known": 0.3, "level": "weak", "last_practiced": datetime.now() - timedelta(days=5)},
    (1, 104): {"p_known": 0.9, "level": "mastered", "last_practiced": datetime.now()},
    (1, 105): {"p_known": 0.5, "level": "learning", "last_practiced": datetime.now() - timedelta(days=3)},
}

# 模拟题目数据
mock_questions = [
    {"id": 1, "content": "等差数列求和", "difficulty": -0.5, "knowledge_point_id": 101},
    {"id": 2, "content": "等比数列通项", "difficulty": 0.0, "knowledge_point_id": 102},
    {"id": 3, "content": "递推数列", "difficulty": 1.0, "knowledge_point_id": 103},
    {"id": 4, "content": "数列极限", "difficulty": 1.5, "knowledge_point_id": 104},
    {"id": 5, "content": "数学归纳法", "difficulty": 0.5, "knowledge_point_id": 105},
]

# 初始化算法模型
bkt_model = BKTModel()
irt_model = IRTModel()
kirt_model = KIRTModel()
adaptive_k = AdaptiveKFactor()
memory_decay = MemoryDecay()
actual_score_calc = ActualScoreCalculator()

# ============ 请求/响应模型 ============

class MasteryUpdateRequest(BaseModel):
    user_id: int
    knowledge_point_id: int
    is_correct: bool

class MasteryUpdateResponse(BaseModel):
    user_id: int
    knowledge_point_id: int
    p_known: float
    mastery_level: str
    consecutive_correct: int = 0
    consecutive_wrong: int = 0

class ThetaEstimateResponse(BaseModel):
    user_id: int
    theta: float
    theta_irt: float
    theta_bkt: float
    alpha: float
    theta_se: float
    ci_lower: float
    ci_upper: float
    level: str

class ActualScoreRequest(BaseModel):
    is_correct: bool
    hint_level: int = Field(..., ge=0, le=4)
    time_spent: float
    expected_time: float
    skip_reason: Optional[str] = None

class ActualScoreResponse(BaseModel):
    actual_score: float
    hint_level_name: str
    components: Dict

class DifficultyRangeResponse(BaseModel):
    user_id: int
    theta: float
    min_difficulty: float
    max_difficulty: float
    recommended_range: str

class MasteryDistribution(BaseModel):
    mastered: int
    learning: int
    weak: int
    total: int

class ComprehensiveReportResponse(BaseModel):
    user_id: int
    ability: Dict
    mastery_distribution: MasteryDistribution
    recommended_difficulty: Dict
    generated_at: str

class QuestionRecommendation(BaseModel):
    question_id: int
    content: str
    difficulty: float
    knowledge_point_id: int
    reason: str

class DailyChallengeResponse(BaseModel):
    user_id: int
    date: str
    questions: List[QuestionRecommendation]
    total_count: int

# ============ API端点 ============

@app.get("/")
def root():
    return {
        "message": "AI Tutor V3 Mock API",
        "version": "3.0.0",
        "status": "running",
        "algorithms": ["BKT", "IRT", "K-IRT", "Adaptive-K", "Memory-Decay", "Actual-Score"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "mock-api"}

# 1. 更新掌握度 (BKT)
@app.post("/api/cognitive/mastery/update", response_model=MasteryUpdateResponse)
def update_mastery(request: MasteryUpdateRequest):
    """更新知识点掌握度（BKT算法）"""
    user_id = request.user_id
    kp_id = request.knowledge_point_id
    
    # 获取当前掌握度
    key = (user_id, kp_id)
    if key in mock_mastery:
        current_p = mock_mastery[key]["p_known"]
        consecutive_correct = mock_mastery[key].get("consecutive_correct", 0)
        consecutive_wrong = mock_mastery[key].get("consecutive_wrong", 0)
    else:
        current_p = 0.5
        consecutive_correct = 0
        consecutive_wrong = 0
    
    # 使用BKT更新
    new_p = bkt_model.update(current_p, request.is_correct)
    
    # 更新连续计数
    if request.is_correct:
        consecutive_correct += 1
        consecutive_wrong = 0
    else:
        consecutive_wrong += 1
        consecutive_correct = 0
    
    # 获取掌握度等级
    level = bkt_model.get_mastery_level(new_p)
    
    # 更新mock数据
    mock_mastery[key] = {
        "p_known": new_p,
        "level": level,
        "last_practiced": datetime.now(),
        "consecutive_correct": consecutive_correct,
        "consecutive_wrong": consecutive_wrong
    }
    
    return MasteryUpdateResponse(
        user_id=user_id,
        knowledge_point_id=kp_id,
        p_known=round(new_p, 4),
        mastery_level=level,
        consecutive_correct=consecutive_correct,
        consecutive_wrong=consecutive_wrong
    )

# 2. 获取能力值 (K-IRT)
@app.get("/api/cognitive/theta/{user_id}", response_model=ThetaEstimateResponse)
def get_theta(user_id: int):
    """获取学生能力值估计（K-IRT联合估算）"""
    if user_id not in mock_users:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user = mock_users[user_id]
    
    # IRT估计
    theta_irt = irt_model.estimate_theta_simple(
        user["correct_count"],
        user["total_questions"]
    )
    
    # BKT映射
    theta_bkt = kirt_model.bkt_mastery_to_theta(user["avg_mastery"])
    
    # K-IRT联合估算
    theta_final = kirt_model.estimate_theta_final(
        theta_irt,
        theta_bkt,
        user["total_questions"]
    )
    
    # 计算alpha
    alpha = kirt_model.compute_alpha(user["total_questions"])
    
    # 计算标准误和置信区间
    theta_se = max(0.05, 1.0 / ((user["total_questions"] + 1) ** 0.5))
    ci_margin = 1.96 * theta_se
    
    # 能力等级
    if theta_final >= 1.0:
        level = "优秀"
    elif theta_final >= 0.0:
        level = "良好"
    elif theta_final >= -1.0:
        level = "一般"
    else:
        level = "需努力"
    
    return ThetaEstimateResponse(
        user_id=user_id,
        theta=round(theta_final, 4),
        theta_irt=round(theta_irt, 4),
        theta_bkt=round(theta_bkt, 4),
        alpha=alpha,
        theta_se=round(theta_se, 4),
        ci_lower=round(theta_final - ci_margin, 4),
        ci_upper=round(theta_final + ci_margin, 4),
        level=level
    )

# 3. 计算Actual Score
@app.post("/api/cognitive/actual-score/calculate", response_model=ActualScoreResponse)
def calculate_actual_score(request: ActualScoreRequest):
    """计算Actual Score"""
    record = AnswerRecord(
        is_correct=request.is_correct,
        hint_level=HintLevel(request.hint_level),
        time_spent=request.time_spent,
        expected_time=request.expected_time,
        skip_reason=request.skip_reason
    )
    
    score = actual_score_calc.calculate(record)
    
    hint_names = {
        0: "自主完成",
        1: "方向提示",
        2: "公式提示",
        3: "步骤推导",
        4: "完整答案"
    }
    
    return ActualScoreResponse(
        actual_score=round(score, 4),
        hint_level_name=hint_names.get(request.hint_level, "未知"),
        components={
            "correctness": request.is_correct,
            "hint_weight": actual_score_calc.params.hint_weights[HintLevel(request.hint_level)],
            "time_ratio": round(request.time_spent / request.expected_time, 2),
            "skip_reason": request.skip_reason
        }
    )

# 4. 获取推荐难度范围
@app.get("/api/cognitive/difficulty-range/{user_id}", response_model=DifficultyRangeResponse)
def get_difficulty_range(user_id: int):
    """获取推荐题目难度范围"""
    if user_id not in mock_users:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    theta = mock_users[user_id]["theta"]
    min_diff, max_diff = irt_model.get_recommended_difficulty_range(theta)
    
    return DifficultyRangeResponse(
        user_id=user_id,
        theta=theta,
        min_difficulty=min_diff,
        max_difficulty=max_diff,
        recommended_range=f"[{min_diff:+.1f}, {max_diff:+.1f}]"
    )

# 5. 获取综合诊断报告
@app.get("/api/cognitive/report/{user_id}", response_model=ComprehensiveReportResponse)
def get_comprehensive_report(user_id: int):
    """获取综合诊断报告"""
    if user_id not in mock_users:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取能力值
    theta_response = get_theta(user_id)
    
    # 统计掌握度分布
    mastered = learning = weak = 0
    for key, data in mock_mastery.items():
        if key[0] == user_id:
            if data["level"] == "mastered":
                mastered += 1
            elif data["level"] == "learning":
                learning += 1
            else:
                weak += 1
    
    # 获取推荐难度
    diff_range = get_difficulty_range(user_id)
    
    return ComprehensiveReportResponse(
        user_id=user_id,
        ability={
            "theta": theta_response.theta,
            "level": theta_response.level,
            "theta_se": theta_response.theta_se
        },
        mastery_distribution=MasteryDistribution(
            mastered=mastered,
            learning=learning,
            weak=weak,
            total=mastered + learning + weak
        ),
        recommended_difficulty={
            "min": diff_range.min_difficulty,
            "max": diff_range.max_difficulty
        },
        generated_at=datetime.now().isoformat()
    )

# 6. 应用记忆衰减
@app.post("/api/cognitive/memory-decay/apply")
def apply_memory_decay(user_id: int):
    """应用记忆衰减"""
    updates = []
    now = datetime.now()
    
    for key, data in list(mock_mastery.items()):
        if key[0] == user_id:
            last_practiced = data.get("last_practiced", now)
            p_decayed = memory_decay.compute_decay_with_timestamp(
                data["p_known"],
                last_practiced,
                now
            )
            
            # 更新mock数据
            mock_mastery[key]["p_known"] = p_decayed
            mock_mastery[key]["level"] = bkt_model.get_mastery_level(p_decayed)
            
            updates.append({
                "knowledge_point_id": key[1],
                "p_known_original": data["p_known"],
                "p_known_decayed": round(p_decayed, 4),
                "days_passed": (now - last_practiced).days
            })
    
    return {
        "user_id": user_id,
        "updated_count": len(updates),
        "updates": updates
    }

# 7. 获取每日闯关题目
@app.get("/api/cognitive/daily-challenge/{user_id}", response_model=DailyChallengeResponse)
def get_daily_challenge(user_id: int):
    """获取每日闯关题目（5道题）"""
    if user_id not in mock_users:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    theta = mock_users[user_id]["theta"]
    min_diff, max_diff = irt_model.get_recommended_difficulty_range(theta)
    
    # 筛选合适难度的题目
    recommended = []
    for q in mock_questions:
        if min_diff <= q["difficulty"] <= max_diff:
            # 计算推荐理由
            diff = abs(q["difficulty"] - theta)
            if diff <= 0.3:
                reason = "精准匹配你的能力水平"
            elif q["difficulty"] > theta:
                reason = "适度挑战，提升能力"
            else:
                reason = "巩固基础，温故知新"
            
            recommended.append(QuestionRecommendation(
                question_id=q["id"],
                content=q["content"],
                difficulty=q["difficulty"],
                knowledge_point_id=q["knowledge_point_id"],
                reason=reason
            ))
    
    # 限制5道题
    recommended = recommended[:5]
    
    return DailyChallengeResponse(
        user_id=user_id,
        date=datetime.now().strftime("%Y-%m-%d"),
        questions=recommended,
        total_count=len(recommended)
    )

# 8. 获取知识点掌握度列表
@app.get("/api/cognitive/mastery/list/{user_id}")
def get_mastery_list(user_id: int):
    """获取用户所有知识点掌握度"""
    result = []
    for key, data in mock_mastery.items():
        if key[0] == user_id:
            result.append({
                "knowledge_point_id": key[1],
                "p_known": round(data["p_known"], 4),
                "mastery_level": data["level"],
                "last_practiced": data.get("last_practiced", datetime.now()).isoformat()
            })
    return {"user_id": user_id, "mastery_list": result}

# 9. 获取用户列表（用于测试）
@app.get("/api/users")
def get_users():
    """获取所有用户（测试用）"""
    return list(mock_users.values())

# 10. 重置用户数据（测试用）
@app.post("/api/users/{user_id}/reset")
def reset_user(user_id: int):
    """重置用户数据（测试用）"""
    if user_id in mock_users:
        mock_users[user_id]["theta"] = 0.0
        mock_users[user_id]["total_questions"] = 0
        mock_users[user_id]["correct_count"] = 0
        mock_users[user_id]["avg_mastery"] = 0.5
    
    # 清除掌握度数据
    keys_to_remove = [k for k in mock_mastery.keys() if k[0] == user_id]
    for k in keys_to_remove:
        del mock_mastery[k]
    
    return {"message": f"用户{user_id}数据已重置"}


if __name__ == "__main__":
    print("=" * 60)
    print("AI Tutor V3 Mock API Server")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  GET  /                          - Root")
    print("  GET  /health                    - Health check")
    print("  POST /api/cognitive/mastery/update         - Update mastery (BKT)")
    print("  GET  /api/cognitive/theta/{user_id}        - Get theta (K-IRT)")
    print("  POST /api/cognitive/actual-score/calculate - Calculate Actual Score")
    print("  GET  /api/cognitive/difficulty-range/{user_id} - Difficulty range")
    print("  GET  /api/cognitive/report/{user_id}       - Comprehensive report")
    print("  POST /api/cognitive/memory-decay/apply     - Apply memory decay")
    print("  GET  /api/cognitive/daily-challenge/{user_id} - Daily challenge")
    print("  GET  /api/cognitive/mastery/list/{user_id} - Mastery list")
    print("  GET  /api/users                 - List users")
    print("  POST /api/users/{user_id}/reset - Reset user data")
    print("\n" + "=" * 60)
    print("Server starting at http://localhost:8001")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
