"""
需求20：每日5题特训包

业务定义（硬指标）：
- 学生每日首次登录时，Advisor Agent自动下发5道题目的固定训练包

动态混排配比规则（强制约束）：
- 温故题 (复习)：1-2题，从Redis Review Queue获取到期题目
- 攻坚题 (薄弱)：2-3题，P(L)<0.5的知识点变式题
- 探索题 (拓展)：1题，符合θ难度区间的全新题目

UI标签：[温故]、[攻坚]、[探索]
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class QuestionType(Enum):
    """题目类型"""
    REVIEW = "review"       # 温故题（复习）
    WEAK = "weak"           # 攻坚题（薄弱）
    EXPLORE = "explore"     # 探索题（拓展）


@dataclass
class DailyQuestion:
    """每日题目"""
    question_id: str
    question_type: QuestionType
    type_label: str           # [温故]/[攻坚]/[探索]
    knowledge_point: str
    difficulty: float         # 题目难度
    reason: str               # 推荐理由
    
    def to_dict(self) -> Dict:
        return {
            "question_id": self.question_id,
            "question_type": self.question_type.value,
            "type_label": self.type_label,
            "knowledge_point": self.knowledge_point,
            "difficulty": round(self.difficulty, 2),
            "reason": self.reason
        }


@dataclass
class DailyTrainingPack:
    """每日特训包"""
    user_id: int
    date: str                 # 日期 YYYY-MM-DD
    total_questions: int = 5  # 固定5题
    questions: List[DailyQuestion] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "date": self.date,
            "total_questions": len(self.questions),
            "questions": [q.to_dict() for q in self.questions],
            "type_distribution": self._get_type_distribution()
        }
    
    def _get_type_distribution(self) -> Dict:
        """获取题型分布统计"""
        dist = {"review": 0, "weak": 0, "explore": 0}
        for q in self.questions:
            dist[q.question_type.value] += 1
        return dist


class DailyTrainingPackGenerator:
    """
    每日特训包生成器
    
    生成规则：
    1. 温故题 (1-2题)：从Redis Review Queue获取到期题目
    2. 攻坚题 (2-3题)：查询P(L)<0.5的知识点，召回变式题
    3. 探索题 (1题)：符合θ难度区间[θ-0.5, θ+0.5]的全新题目
    """
    
    # 配比规则（硬指标）
    REVIEW_COUNT = (1, 2)      # 温故题：1-2题
    WEAK_COUNT = (2, 3)        # 攻坚题：2-3题
    EXPLORE_COUNT = (1, 1)     # 探索题：1题
    TOTAL_QUESTIONS = 5        # 总计5题
    
    # 题型标签
    TYPE_LABELS = {
        QuestionType.REVIEW: "[温故]",
        QuestionType.WEAK: "[攻坚]",
        QuestionType.EXPLORE: "[探索]"
    }
    
    def __init__(self):
        # Mock数据：题目库
        self.mock_question_bank = self._init_mock_question_bank()
    
    def _init_mock_question_bank(self) -> Dict[str, List[Dict]]:
        """初始化Mock题目库"""
        return {
            "等差数列": [
                {"id": "q001", "kp": "等差数列定义", "difficulty": 0.2},
                {"id": "q002", "kp": "等差数列通项", "difficulty": 0.5},
                {"id": "q003", "kp": "等差数列求和", "difficulty": 0.8},
            ],
            "等比数列": [
                {"id": "q004", "kp": "等比数列定义", "difficulty": 0.3},
                {"id": "q005", "kp": "等比数列通项", "difficulty": 0.6},
                {"id": "q006", "kp": "等比数列求和", "difficulty": 0.9},
            ],
            "数列综合": [
                {"id": "q007", "kp": "递推数列", "difficulty": 0.7},
                {"id": "q008", "kp": "数列极限", "difficulty": 1.2},
                {"id": "q009", "kp": "数列应用", "difficulty": 1.5},
            ]
        }
    
    def generate_pack(
        self,
        user_id: int,
        user_theta: float,
        user_mastery: Dict[str, float],
        review_queue: List[str] = None,
        date: str = None
    ) -> DailyTrainingPack:
        """
        生成每日特训包
        
        Args:
            user_id: 用户ID
            user_theta: 用户能力值
            user_mastery: {knowledge_point: p_known}
            review_queue: Redis Review Queue中的题目ID列表
            date: 日期字符串
            
        Returns:
            每日特训包
        """
        from datetime import datetime
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if review_queue is None:
            review_queue = []
        
        pack = DailyTrainingPack(user_id=user_id, date=date)
        questions = []
        used_question_ids = set()
        
        # 1. 选取温故题 (1-2题)
        review_count = random.randint(*self.REVIEW_COUNT)
        review_questions = self._select_review_questions(
            review_queue, review_count, used_question_ids
        )
        questions.extend(review_questions)
        
        # 2. 选取攻坚题 (2-3题)
        weak_count = random.randint(*self.WEAK_COUNT)
        weak_questions = self._select_weak_questions(
            user_mastery, user_theta, weak_count, used_question_ids
        )
        questions.extend(weak_questions)
        
        # 3. 选取探索题 (1题)
        explore_count = random.randint(*self.EXPLORE_COUNT)
        explore_questions = self._select_explore_questions(
            user_theta, explore_count, used_question_ids
        )
        questions.extend(explore_questions)
        
        # 如果不足5题，用探索题补足
        while len(questions) < self.TOTAL_QUESTIONS:
            extra = self._select_explore_questions(
                user_theta, 1, used_question_ids
            )
            questions.extend(extra)
        
        # 只取前5题
        pack.questions = questions[:self.TOTAL_QUESTIONS]
        
        return pack
    
    def _select_review_questions(
        self,
        review_queue: List[str],
        count: int,
        used_ids: set
    ) -> List[DailyQuestion]:
        """选取温故题（从Review Queue）"""
        questions = []
        
        for qid in review_queue:
            if len(questions) >= count:
                break
            if qid in used_ids:
                continue
            
            # Mock：从题目库查找
            for topic, qs in self.mock_question_bank.items():
                for q in qs:
                    if q["id"] == qid:
                        questions.append(DailyQuestion(
                            question_id=qid,
                            question_type=QuestionType.REVIEW,
                            type_label=self.TYPE_LABELS[QuestionType.REVIEW],
                            knowledge_point=q["kp"],
                            difficulty=q["difficulty"],
                            reason="距离上次做错已过去2天，测测肌肉记忆还在不在？"
                        ))
                        used_ids.add(qid)
                        break
        
        return questions
    
    def _select_weak_questions(
        self,
        user_mastery: Dict[str, float],
        user_theta: float,
        count: int,
        used_ids: set
    ) -> List[DailyQuestion]:
        """选取攻坚题（P(L)<0.5的知识点）"""
        questions = []
        
        # 找出薄弱知识点
        weak_kps = [kp for kp, p in user_mastery.items() if p < 0.5]
        
        for kp in weak_kps:
            if len(questions) >= count:
                break
            
            # 从题目库找该知识点的题目
            for topic, qs in self.mock_question_bank.items():
                for q in qs:
                    if q["kp"] == kp and q["id"] not in used_ids:
                        questions.append(DailyQuestion(
                            question_id=q["id"],
                            question_type=QuestionType.WEAK,
                            type_label=self.TYPE_LABELS[QuestionType.WEAK],
                            knowledge_point=kp,
                            difficulty=q["difficulty"],
                            reason=f"你在【{kp}】方面还需要加强，这道题正好匹配你的水平。"
                        ))
                        used_ids.add(q["id"])
                        break
        
        return questions
    
    def _select_explore_questions(
        self,
        user_theta: float,
        count: int,
        used_ids: set
    ) -> List[DailyQuestion]:
        """选取探索题（符合θ难度区间的全新题目）"""
        questions = []
        
        # 难度区间 [θ-0.5, θ+0.5]
        min_diff = user_theta - 0.5
        max_diff = user_theta + 0.5
        
        # 从题目库找符合难度区间的题目
        for topic, qs in self.mock_question_bank.items():
            for q in qs:
                if len(questions) >= count:
                    break
                if q["id"] in used_ids:
                    continue
                if min_diff <= q["difficulty"] <= max_diff:
                    questions.append(DailyQuestion(
                        question_id=q["id"],
                        question_type=QuestionType.EXPLORE,
                        type_label=self.TYPE_LABELS[QuestionType.EXPLORE],
                        knowledge_point=q["kp"],
                        difficulty=q["difficulty"],
                        reason="这道进阶题能帮你更上一层楼，敢不敢挑战一下？"
                    ))
                    used_ids.add(q["id"])
        
        return questions


# 全局生成器实例
daily_pack_generator = DailyTrainingPackGenerator()


def get_daily_pack_generator() -> DailyTrainingPackGenerator:
    """获取生成器实例"""
    return daily_pack_generator


# 单元测试
if __name__ == "__main__":
    print("=== 需求20：每日5题特训包测试 ===\n")
    
    generator = DailyTrainingPackGenerator()
    
    # Mock用户数据
    user_id = 1
    user_theta = 0.5
    user_mastery = {
        "等差数列定义": 0.9,
        "等差数列通项": 0.85,
        "等差数列求和": 0.3,  # 薄弱
        "等比数列定义": 0.4,  # 薄弱
        "递推数列": 0.6,
    }
    review_queue = ["q001"]  # 假设有1道到期复习题
    
    # 生成特训包
    pack = generator.generate_pack(
        user_id=user_id,
        user_theta=user_theta,
        user_mastery=user_mastery,
        review_queue=review_queue
    )
    
    print(f"用户ID: {pack.user_id}")
    print(f"日期: {pack.date}")
    print(f"总题数: {pack.total_questions}")
    print(f"题型分布: {pack._get_type_distribution()}")
    print("\n题目列表:")
    
    for i, q in enumerate(pack.questions, 1):
        print(f"\n  第{i}题:")
        print(f"    标签: {q.type_label}")
        print(f"    知识点: {q.knowledge_point}")
        print(f"    难度: {q.difficulty}")
        print(f"    推荐理由: {q.reason}")
    
    print("\n=== 测试完成！===")
