import json
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError

from models.profile import UserProfile

from models.question import Question
from models.record import LearningRecord
from services.learning_analytics_service import estimate_theta, process_answer_analytics
from services.record_service import save_recommended_question_record

RECOMMENDATION_ALGORITHM_V1 = "v1.0"
RECOMMENDATION_ALGORITHM_V2 = "v2.0"
RECOMMENDATION_ALGORITHM_CONTROL = "control"
RECOMMENDATION_ALGORITHM_TREATMENT = "treatment"
DEFAULT_ALGORITHM_VERSION = RECOMMENDATION_ALGORITHM_V1


def _normalize_algorithm_version(user_id: int, algorithm_version: Optional[str]) -> str:
    if algorithm_version:
        return algorithm_version
    return RECOMMENDATION_ALGORITHM_TREATMENT if user_id % 2 == 0 else RECOMMENDATION_ALGORITHM_CONTROL


def _sort_topics_v1(weak_data: Dict[str, int]) -> List[Tuple[str, float]]:
    return [(k, float(v)) for k, v in sorted(weak_data.items(), key=lambda x: x[1], reverse=True)]


def _sort_topics_v2(weak_data: Dict[str, int], mastery_data: Optional[Dict]) -> List[Tuple[str, float]]:
    if mastery_data is None:
        mastery_data = {}
    if isinstance(mastery_data, str):
        try:
            mastery_data = json.loads(mastery_data)
        except Exception:
            mastery_data = {}

    scored_topics = []
    for topic, error_count in weak_data.items():
        mastery = mastery_data.get(topic, 0.5)
        if not isinstance(mastery, (int, float)):
            mastery = 0.5
        scored_topics.append((topic, float(error_count) * (1 - float(mastery))))

    scored_topics.sort(key=lambda x: x[1], reverse=True)
    return scored_topics


def _difficulty_match_score(theta: float, question_difficulty: int) -> float:
    diff = abs(float(question_difficulty) - float(theta))
    if diff <= 0.5:
        return 1.0
    if diff >= 2.0:
        return 0.0
    return round(1 - ((diff - 0.5) / 1.5), 4)


def _kp_relevance_score(question_topics: List[str], topic_priority: Dict[str, float]) -> float:
    if not question_topics:
        return 0.0
    total = 0.0
    hit = 0
    for topic in question_topics:
        score = float(topic_priority.get(topic, 0.0))
        if score > 0:
            total += score
            hit += 1
    if hit == 0:
        return 0.0
    max_priority = max(topic_priority.values()) if topic_priority else 1.0
    return min(1.0, (total / hit) / (max_priority if max_priority > 0 else 1.0))


def _recommendation_tone(theta: float, question_difficulty: int) -> str:
    if question_difficulty - theta >= 1:
        return "鼓励型"
    if theta - question_difficulty >= 1:
        return "激励型"
    return "中性"


async def recommend_exercises(
    db: AsyncSession,
    user_id: int,
    limit: int = 5,
    algorithm_version: Optional[str] = None,
) -> List[Dict]:
    algorithm_version = _normalize_algorithm_version(user_id, algorithm_version)

    profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    profile_result = await db.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()
    if not profile or not profile.weak_points:
        return []

    weak_data = profile.weak_points
    if isinstance(weak_data, str):
        try:
            weak_data = json.loads(weak_data)
        except Exception:
            weak_data = {}
    if not isinstance(weak_data, dict) or not weak_data:
        return []

    if algorithm_version in (RECOMMENDATION_ALGORITHM_V2, RECOMMENDATION_ALGORITHM_TREATMENT):
        sorted_topics = _sort_topics_v2(weak_data, profile.knowledge_mastery)
    else:
        sorted_topics = _sort_topics_v1(weak_data)

    target_topics = [topic for topic, _ in sorted_topics]
    topic_priority = {topic: score for topic, score in sorted_topics}
    if not target_topics:
        return []

    total_questions = int(profile.total_questions or 0)
    correct_count = int(profile.correct_count or 0)
    mastery_map = profile.knowledge_mastery or {}
    if not isinstance(mastery_map, dict):
        mastery_map = {}
    avg_mastery = sum(float(v) for v in mastery_map.values()) / len(mastery_map) if mastery_map else 0.5

    theta = estimate_theta(total_questions, correct_count, avg_mastery)["theta"]

    all_questions_stmt = select(Question).where(Question.knowledge_points.isnot(None))
    all_questions_result = await db.execute(all_questions_stmt)
    all_questions = all_questions_result.scalars().all()

    recent_records_stmt = (
        select(LearningRecord.question_id)
        .where(and_(LearningRecord.user_id == user_id, LearningRecord.question_id.is_not(None)))
        .order_by(LearningRecord.created_at.desc())
        .limit(50)
    )
    recent_result = await db.execute(recent_records_stmt)
    done_question_ids = {row[0] for row in recent_result.fetchall() if row[0] is not None}

    scored_candidates: List[Tuple[Question, float, float, float, float]] = []
    for q in all_questions:
        if q.id in done_question_ids:
            continue

        q_topics = q.knowledge_points or []
        if isinstance(q_topics, str):
            try:
                q_topics = json.loads(q_topics)
            except Exception:
                q_topics = []
        if not isinstance(q_topics, list):
            q_topics = []

        if not any(topic in q_topics for topic in target_topics):
            continue

        kp_relevance = _kp_relevance_score([str(t) for t in q_topics], topic_priority)
        difficulty_match = _difficulty_match_score(theta=theta, question_difficulty=int(q.difficulty or 1))
        context_similarity = 0.0
        final_score = 0.6 * kp_relevance + 0.3 * difficulty_match + 0.1 * context_similarity
        scored_candidates.append((q, final_score, kp_relevance, difficulty_match, context_similarity))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    scored_candidates = scored_candidates[:limit]

    recommended_list = []
    for q, final_score, kp_relevance, difficulty_match, context_similarity in scored_candidates:
        recommended_list.append(
            {
                "id": q.id,
                "type": q.question_type,
                "content": q.content,
                "difficulty": q.difficulty,
                "knowledge_points": q.knowledge_points or [],
                "image_url": None,
                "algorithm_version": algorithm_version,
                "theta_target": round(theta, 4),
                "scores": {
                    "final_score": round(final_score, 4),
                    "kp_relevance": round(kp_relevance, 4),
                    "difficulty_match": round(difficulty_match, 4),
                    "context_similarity": round(context_similarity, 4),
                },
                "tone": _recommendation_tone(theta, int(q.difficulty or 1)),
            }
        )

    return recommended_list


async def record_recommendation_result(
    db: AsyncSession,
    user_id: int,
    question_id: int,
    user_answer: str,
    is_correct: bool,
    algorithm_version: str,
    recommendation_session_id: Optional[str] = None,
) -> LearningRecord:
    stmt = select(Question).where(Question.id == question_id)
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    if not question:
        raise ValueError(f"题目不存在: question_id={question_id}")

    analytics = await process_answer_analytics(db=db, user_id=user_id, question=question, is_correct=is_correct)
    theta_data = analytics.get("theta_data", {})
    mastery_updates = analytics.get("mastery_updates", {})

    record = await save_recommended_question_record(
        db=db,
        user_id=user_id,
        question=question,
        answer=user_answer,
        is_correct=is_correct,
        recommendation_algorithm_version=algorithm_version,
        recommendation_session_id=recommendation_session_id,
        theta_before=theta_data.get("theta"),
        theta_after=theta_data.get("theta"),
        mastery_updates=mastery_updates,
    )
    return record


async def get_recommendation_ab_test_stats(
    db: AsyncSession,
    algorithm_version: str,
    limit: int = 1000,
) -> Dict:
    stmt = (
        select(LearningRecord)
        .where(LearningRecord.recommendation_algorithm_version == algorithm_version)
        .order_by(LearningRecord.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    if not records:
        return {
            "algorithm_version": algorithm_version,
            "total_records": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "avg_difficulty": 0.0,
            "avg_time_spent": 0.0,
        }

    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    accuracy = correct / total if total > 0 else 0.0

    question_ids = [r.question_id for r in records if r.question_id is not None]
    avg_difficulty = 0.0
    if question_ids:
        q_stmt = select(func.avg(Question.difficulty)).where(Question.id.in_(question_ids))
        q_result = await db.execute(q_stmt)
        avg_difficulty = float(q_result.scalar() or 0.0)

    valid_time_spent = [int(r.time_spent) for r in records if isinstance(r.time_spent, int)]
    avg_time_spent = sum(valid_time_spent) / len(valid_time_spent) if valid_time_spent else 0.0

    return {
        "algorithm_version": algorithm_version,
        "total_records": total,
        "correct_count": correct,
        "accuracy": round(accuracy, 4),
        "avg_difficulty": round(avg_difficulty, 4),
        "avg_time_spent": round(avg_time_spent, 2),
    }
