"""
Advisor Agent
==============
核心职责（参考 docs/list.md §3 & docs/function.md §三）：
1. 画像初始化  — 用户首次访问时构建基础画像并同步至 Redis
2. 主动推荐    — 从 MySQL 候选池 + Redis 去重/复习队列中选出最优题目
3. 答题反馈    — 更新 BKT/IRT、写回 Redis（Mastery Hash / Review ZSet / Seen Set）
4. 策略调控    — 根据掌握度判断 MODE_SCAFFOLD / MODE_CHALLENGE / MODE_ENCOURAGE
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.learning_analytics import MistakeBook, UserAbilityHistory
from models.profile import UserProfile
from models.question import Question
from models.record import LearningRecord
from services.learning_analytics_service import (
    estimate_theta,
    process_answer_analytics,
)
from services.profile_service import update_user_profile
from utils import redis_client as rc
from utils.logger import logger

# ---------------------------------------------------------------------------
# 难度匹配分
# ---------------------------------------------------------------------------

def _difficulty_match(theta: float, q_difficulty: int) -> float:
    diff = abs(float(q_difficulty) - theta)
    if diff <= 0.5:
        return 1.0
    if diff >= 2.0:
        return 0.0
    return round(1.0 - (diff - 0.5) / 1.5, 4)


def _kp_relevance(q_topics: List[str], weak_kps: List[str]) -> float:
    if not q_topics or not weak_kps:
        return 0.0
    weak_set = set(weak_kps)
    hits = sum(1 for t in q_topics if t in weak_set)
    return round(hits / len(q_topics), 4)


# ---------------------------------------------------------------------------
# 画像初始化 / 冷启动
# ---------------------------------------------------------------------------

async def init_user_profile(db: AsyncSession, user_id: int) -> Dict:
    """
    用户首次使用时初始化基础画像：
    - 检查 MySQL user_profiles 是否存在，不存在则创建（默认参数）
    - 从已有 learning_records 重建 Seen Set
    - 将现有 knowledge_mastery 同步至 Redis Mastery Hash
    返回画像字典
    """
    # 1. 确保 user_profiles 行存在
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(
            user_id=user_id,
            total_questions=0,
            correct_count=0,
            knowledge_mastery={},
            weak_points={},
            theta_se=None,
            theta_ci_lower=None,
            theta_ci_upper=None,
            avg_mastery=0.5,
            weak_kp_count=0,
            learning_style=None,
            mastery_strategy="simple",
        )
        db.add(profile)
        await db.flush()
        logger.info(f"[Advisor] Created initial profile for user_id={user_id}")

    # 2. 从 learning_records 重建 Seen Set（最近 500 条）
    seen_stmt = (
        select(LearningRecord.question_id)
        .where(
            and_(
                LearningRecord.user_id == user_id,
                LearningRecord.question_id.is_not(None),
            )
        )
        .order_by(LearningRecord.created_at.desc())
        .limit(500)
    )
    seen_result = await db.execute(seen_stmt)
    seen_ids = [row[0] for row in seen_result.fetchall() if row[0]]
    if seen_ids:
        await rc.seen_rebuild_from_mysql(user_id, seen_ids)

    # 3. 同步 knowledge_mastery -> Redis Hash
    mastery_map = profile.knowledge_mastery or {}
    if isinstance(mastery_map, dict) and mastery_map:
        await rc.mastery_set_bulk(user_id, mastery_map)

    # 4. 同步 MistakeBook -> Redis Review ZSet（尚未掌握的错题）
    mb_stmt = (
        select(MistakeBook)
        .where(
            and_(
                MistakeBook.user_id == user_id,
                MistakeBook.mastered.is_(False),
                MistakeBook.next_review_at.is_not(None),
            )
        )
    )
    mb_result = await db.execute(mb_stmt)
    mistakes = mb_result.scalars().all()
    for m in mistakes:
        if m.next_review_at:
            ts = m.next_review_at.timestamp()
            await rc.review_add(user_id, m.question_id, ts)

    await db.commit()

    # 5. 缓存画像快照
    profile_dict = _profile_to_dict(profile)
    await rc.profile_cache_set(user_id, profile_dict)

    logger.info(
        f"[Advisor] Profile initialized uid={user_id}, "
        f"seen={len(seen_ids)}, mastery_kps={len(mastery_map)}, mistakes={len(mistakes)}"
    )
    return profile_dict


def _profile_to_dict(profile: UserProfile) -> Dict:
    total = int(profile.total_questions or 0)
    correct = int(profile.correct_count or 0)
    mastery_map = profile.knowledge_mastery or {}
    if not isinstance(mastery_map, dict):
        mastery_map = {}
    avg_mastery = (
        sum(float(v) for v in mastery_map.values()) / len(mastery_map)
        if mastery_map
        else 0.5
    )
    theta_data = estimate_theta(total, correct, avg_mastery)
    return {
        "user_id": profile.user_id,
        "total_questions": total,
        "correct_count": correct,
        "accuracy": round(correct / total * 100, 2) if total > 0 else 0.0,
        "theta": theta_data["theta"],
        "theta_se": theta_data["theta_se"],
        "avg_mastery": round(avg_mastery, 4),
        "weak_kp_count": int(profile.weak_kp_count or 0),
        "knowledge_mastery": mastery_map,
        "weak_points": profile.weak_points or {},
        "learning_style": profile.learning_style,
    }


# ---------------------------------------------------------------------------
# 推荐引擎
# ---------------------------------------------------------------------------

# 探索 / 利用配比：70% 新题 / 30% 复习题
EXPLORE_RATIO = 0.7

async def get_advisor_recommendations(
    db: AsyncSession,
    user_id: int,
    limit: int = 5,
) -> Dict:
    """
    完整 Advisor 推荐流程：
    1. 读取 Redis 画像缓存（降级读 MySQL）
    2. 从 Redis 获取 due 复习题（优先）
    3. 从 MySQL 候选池构建 + Redis Seen Set 去重
    4. 打分排序
    5. 探索/利用混合
    返回：{ recommendations: [...], advisor_mode: str, profile_snapshot: {...} }
    """
    # --- Step 1: 画像快照 ---
    profile_dict = await rc.profile_cache_get(user_id)
    if not profile_dict:
        profile_dict = await init_user_profile(db, user_id)

    theta = float(profile_dict.get("theta") or 3.0)
    mastery_map = profile_dict.get("knowledge_mastery") or {}
    weak_points = profile_dict.get("weak_points") or {}

    # --- Step 2: 从 Redis 读取 due 复习题 ---
    due_review_ids = await rc.review_get_due(user_id, limit=max(1, int(limit * (1 - EXPLORE_RATIO)) + 1))
    logger.info(f"[Advisor] uid={user_id} due_reviews={due_review_ids}")

    # --- Step 3: 薄弱知识点排序 ---
    weak_kps = await rc.mastery_get_weakest(user_id, top_n=5)
    if not weak_kps:
        # 降级：用 profile weak_points
        weak_kps = sorted(weak_points.keys(), key=lambda k: weak_points[k], reverse=True)[:5]

    # --- Step 4: MySQL 候选池 ---
    # 从 Seen Set 拿到已做列表用于过滤
    seen_ids = await rc.seen_get_all(user_id)
    # 加上 due_review_ids（这些可以重新推送复习）
    seen_ids_for_new = seen_ids - {int(i) for i in due_review_ids}

    all_q_stmt = select(Question).where(Question.knowledge_points.isnot(None))
    all_q_result = await db.execute(all_q_stmt)
    all_questions = all_q_result.scalars().all()

    # --- Step 5: 新题候选打分 ---
    explore_target = max(1, int(limit * EXPLORE_RATIO) + 1)
    new_candidates: List[Tuple[Question, float]] = []

    for q in all_questions:
        if q.id in seen_ids_for_new:
            continue
        q_topics = _normalize_topics(q.knowledge_points)
        if weak_kps and not any(t in weak_kps for t in q_topics):
            continue  # 优先知识点相关

        kp_rel = _kp_relevance(q_topics, weak_kps)
        diff_match = _difficulty_match(theta, int(q.difficulty or 1))
        score = 0.6 * kp_rel + 0.3 * diff_match + 0.1 * 0.0  # context_similarity 暂为 0
        new_candidates.append((q, score))

    new_candidates.sort(key=lambda x: x[1], reverse=True)
    new_candidates = new_candidates[:explore_target]

    # --- Step 6: 复习题填充 ---
    review_questions: List[Question] = []
    if due_review_ids:
        review_stmt = select(Question).where(Question.id.in_([int(i) for i in due_review_ids]))
        review_result = await db.execute(review_stmt)
        review_questions = review_result.scalars().all()

    # --- Step 7: 合并（复习优先） ---
    review_slot = max(0, limit - len(new_candidates))
    final_review = review_questions[:review_slot]
    final_new = new_candidates[:limit - len(final_review)]

    # --- Step 8: 判断 Advisor 模式 ---
    avg_mastery = float(profile_dict.get("avg_mastery") or 0.5)
    total_questions = int(profile_dict.get("total_questions") or 0)
    weak_kp_count = int(profile_dict.get("weak_kp_count") or 0)

    advisor_mode = _determine_advisor_mode(avg_mastery, weak_kp_count)

    # --- Step 9: 组装返回 ---
    result_list = []

    for q in final_review:
        q_topics = _normalize_topics(q.knowledge_points)
        result_list.append(_build_recommendation_item(
            q, theta, q_topics, weak_kps, is_review=True, advisor_mode=advisor_mode
        ))

    for q, score in final_new:
        q_topics = _normalize_topics(q.knowledge_points)
        result_list.append(_build_recommendation_item(
            q, theta, q_topics, weak_kps, is_review=False, advisor_mode=advisor_mode, base_score=score
        ))

    logger.info(
        f"[Advisor] uid={user_id} recommended {len(result_list)} questions, "
        f"review={len(final_review)}, new={len(final_new)}, mode={advisor_mode}"
    )

    return {
        "recommendations": result_list,
        "advisor_mode": advisor_mode,
        "advisor_instruction": _build_instruction(advisor_mode, weak_kps, theta),
        "profile_snapshot": {
            "theta": round(theta, 3),
            "avg_mastery": round(avg_mastery, 3),
            "weak_kps": weak_kps[:3],
            "total_questions": total_questions,
        },
    }


def _normalize_topics(raw) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(t).strip() for t in parsed if str(t).strip()]
        except Exception:
            pass
    return []


def _determine_advisor_mode(avg_mastery: float, weak_kp_count: int) -> str:
    """
    MODE_SCAFFOLD  : avg_mastery < 0.4 或 薄弱知识点 > 3
    MODE_CHALLENGE : avg_mastery > 0.8 且 weak_kp_count <= 1
    MODE_ENCOURAGE : 其他（中间状态）
    """
    if avg_mastery < 0.4 or weak_kp_count > 3:
        return "MODE_SCAFFOLD"
    if avg_mastery > 0.8 and weak_kp_count <= 1:
        return "MODE_CHALLENGE"
    return "MODE_ENCOURAGE"


def _build_instruction(mode: str, weak_kps: List[str], theta: float) -> Dict:
    kps_str = "、".join(weak_kps[:3]) if weak_kps else "综合知识点"
    if mode == "MODE_SCAFFOLD":
        return {
            "instruction": mode,
            "reasoning": f"当前薄弱知识点为【{kps_str}】，建议分步讲解，逐步引导",
            "control_params": {
                "hint_level": "L2",
                "step_by_step": True,
                "allow_skip": True,
            },
            "tone": "鼓励型",
        }
    if mode == "MODE_CHALLENGE":
        return {
            "instruction": mode,
            "reasoning": f"学生能力值θ={theta:.2f}，整体掌握较好，给予挑战性题目",
            "control_params": {
                "hint_level": "L0",
                "step_by_step": False,
                "allow_skip": False,
            },
            "tone": "激励型",
        }
    return {
        "instruction": mode,
        "reasoning": f"学生正在学习【{kps_str}】，给予适度引导和鼓励",
        "control_params": {
            "hint_level": "L1",
            "step_by_step": True,
            "encouragement": True,
        },
        "tone": "中性",
    }


def _build_recommendation_item(
    q: Question,
    theta: float,
    q_topics: List[str],
    weak_kps: List[str],
    is_review: bool,
    advisor_mode: str,
    base_score: float = 0.0,
) -> Dict:
    diff_match = _difficulty_match(theta, int(q.difficulty or 1))
    kp_rel = _kp_relevance(q_topics, weak_kps)
    final_score = base_score if base_score > 0 else (0.6 * kp_rel + 0.3 * diff_match)

    # 推荐语气
    diff = int(q.difficulty or 1)
    if diff - theta >= 1:
        tone = "鼓励型"
        reason_suffix = "是一道有挑战性的题目，相信你能做到！"
    elif theta - diff >= 1:
        tone = "激励型"
        reason_suffix = "和你最近做过的题目类型相似，试试能不能举一反三？"
    else:
        tone = "中性"
        reason_suffix = "正好匹配你当前的能力水平。"

    weak_kp_hit = [t for t in q_topics if t in set(weak_kps)]
    if weak_kp_hit:
        reason = f"你在【{weak_kp_hit[0]}】方面还需加强，这道题{reason_suffix}"
    else:
        reason = f"这道题{reason_suffix}"

    if is_review:
        reason = "这道题之前做错了，现在是复习它的好时机！" + reason

    return {
        "id": q.id,
        "content": q.content,
        "difficulty": q.difficulty,
        "knowledge_points": q_topics,
        "question_type": q.question_type,
        "is_review": is_review,
        "advisor_mode": advisor_mode,
        "scores": {
            "final_score": round(final_score, 4),
            "kp_relevance": round(kp_rel, 4),
            "difficulty_match": round(diff_match, 4),
        },
        "tone": tone,
        "recommendation_reason": reason,
    }


# ---------------------------------------------------------------------------
# 答题反馈闭环
# ---------------------------------------------------------------------------

async def record_answer_feedback(
    db: AsyncSession,
    user_id: int,
    question_id: int,
    is_correct: bool,
    hint_count: int = 0,
    time_spent: Optional[int] = None,
    skip_reason: Optional[str] = None,
    algorithm_version: str = "advisor-v1",
    recommendation_session_id: Optional[str] = None,
) -> Dict:
    """
    答题后的完整 Advisor 反馈闭环：
    1. 标记题目为已做 -> Redis Seen Set
    2. 更新 BKT/IRT/画像 -> MySQL + Redis Mastery Hash
    3. 更新错题复习队列 -> Redis Review ZSet + MySQL MistakeBook
    4. 失效画像缓存，促使下次重新加载
    5. 跳过行为处理（too_easy / too_hard）
    返回 { theta_data, mastery_updates, advisor_action }
    """
    # 1. 标记 Seen
    await rc.seen_add(user_id, question_id)

    # 2. 加载题目
    q_stmt = select(Question).where(Question.id == question_id)
    q_result = await db.execute(q_stmt)
    question = q_result.scalar_one_or_none()

    if not question:
        logger.warning(f"[Advisor] record_answer: question {question_id} not found")
        return {"error": f"question {question_id} not found"}

    # 3. 跳过处理
    advisor_action = "continue"
    if skip_reason == "too_easy":
        is_correct = True
        advisor_action = "escalate"
    elif skip_reason == "too_hard":
        is_correct = False
        advisor_action = "deescalate"

    # 4. 调用统一分析（更新 BKT/IRT/错题本/能力历史）
    analytics = await process_answer_analytics(
        db=db,
        user_id=user_id,
        question=question,
        is_correct=is_correct,
    )
    theta_data = analytics.get("theta_data", {})
    mastery_updates = analytics.get("mastery_updates", {})

    # 5. 同步掌握度到 Redis Hash
    if mastery_updates:
        await rc.mastery_set_bulk(user_id, mastery_updates)

    # 6. 更新 Redis Review ZSet
    #    做错 -> 加入/更新复习队列；做对且存在 -> 移除
    if not is_correct:
        # 指数退避：从 MistakeBook 读取 error_count
        mb_stmt = select(MistakeBook).where(
            and_(MistakeBook.user_id == user_id, MistakeBook.question_id == question_id)
        )
        mb_result = await db.execute(mb_stmt)
        mb = mb_result.scalar_one_or_none()
        error_count = int(mb.error_count or 1) if mb else 1
        days = 2 ** max(0, error_count - 1)
        next_review_ts = time.time() + days * 86400
        await rc.review_add(user_id, question_id, next_review_ts)
    else:
        await rc.review_remove(user_id, question_id)

    # 7. 失效画像缓存
    await rc.profile_cache_invalidate(user_id)

    # 8. 保存详细学习记录（hint_count / time_spent / skip_reason）
    record = LearningRecord(
        user_id=user_id,
        question_id=question_id,
        source_type="recommended",
        is_correct=is_correct,
        hint_count=hint_count,
        time_spent=time_spent,
        skip_reason=skip_reason,
        theta_before=theta_data.get("theta"),
        theta_after=theta_data.get("theta"),
        mastery_updates=mastery_updates,
        recommendation_algorithm_version=algorithm_version,
        recommendation_session_id=recommendation_session_id,
    )
    db.add(record)
    await db.commit()

    logger.info(
        f"[Advisor] feedback uid={user_id} qid={question_id} correct={is_correct} "
        f"skip={skip_reason} theta={theta_data.get('theta')} action={advisor_action}"
    )

    return {
        "theta_data": theta_data,
        "mastery_updates": mastery_updates,
        "advisor_action": advisor_action,
        "record_id": record.id,
    }
