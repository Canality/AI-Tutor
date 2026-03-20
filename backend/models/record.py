from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, String, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base


class LearningRecord(Base):
    """
    学习记录模型 - 双模态存储设计

    【核心设计原则 - 双模态互斥关系】
    ========================================
    本模型支持两种互斥的数据存储模式，通过 source_type 字段区分：

    模式 A: 系统题库题 (source_type = 'recommended' 或 'practice')
    --------------------------------------------------------------------
    - question_id: 必填 (外键关联 questions.id)
    - custom_question_data: 必须为 NULL
    - is_correct: 必填 (布尔值，表示答题是否正确)

    模式 B: 用户上传题 (source_type = 'uploaded')
    --------------------------------------------------------------------
    - question_id: 必须为 NULL
    - custom_question_data: 必填 (JSON 格式，复刻 questions 表结构)
    - is_correct: 可空 (用户上传题可能无标准答案，需 AI 评估)

    【JSON Schema 约束 (custom_question_data)】
    ========================================
    {
        "content": "题目内容文本",           # 必填，对应 questions.content
        "standard_answer": "标准答案",       # 可选，对应 questions.standard_answer
        "difficulty": 2,                     # 可选，对应 questions.difficulty (1-5)
        "question_type": "single_choice",    # 可选，对应 questions.question_type
        "knowledge_points": ["方程", "一元一次"]  # 可选，对应 questions.knowledge_points
    }

    【A/B 测试支持】
    ========================================
    - recommendation_algorithm_version: 记录推荐算法版本，用于对比实验
    """
    __tablename__ = "learning_records"

    # --- 基础主键 ---
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # --- 双模态字段 1: 题目关联 (模式 A 必填，模式 B 为 NULL) ---
    # 外键关联 questions.id，仅当 source_type = 'recommended'/'practice' 时有值
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)

    # --- 双模态字段 2: 来源标识 ---
    # 枚举值: 'uploaded' (用户上传), 'recommended' (系统推荐), 'practice' (随机练习)
    source_type = Column(String(50), nullable=False, default='recommended', index=True)

    # --- 双模态字段 3: 自定义题目数据 (模式 B 必填，模式 A 为 NULL) ---
    # 当 question_id 为 NULL 时，此处存储完整的题目数据 (JSON 格式)
    # 结构必须符合 CustomQuestionData Schema (见 schemas/question.py)
    custom_question_data = Column(JSON, nullable=True)

    # --- 答题情况 ---
    # 模式 A 必填；模式 B 可空（用户上传题可能需 AI 评估后才能确定对错）
    is_correct = Column(Boolean, nullable=True)
    user_answer = Column(Text, nullable=True)  # 学生的作答内容

    # AI 反馈或解析 (无论哪种来源，都可以存储 AI 生成的解析)
    ai_feedback = Column(Text, nullable=True)

    # --- 推荐上下文 (针对推荐题) ---
    # 记录这次做题是属于哪一次推荐会话，用于分析推荐算法效果
    recommendation_session_id = Column(String(100), nullable=True, index=True)

    # --- A/B 测试支持: 推荐算法版本 ---
    # 用于记录生成此推荐的算法版本，支持 A/B 测试和效果追踪
    # 示例值: "v1.0", "v2.0-experimental", "control", "treatment"
    recommendation_algorithm_version = Column(String(50), nullable=True, index=True)

    # --- 时间戳 ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- 关系定义 ---
    # back_populates 需要在 User 模型中也对应添加
    user = relationship("User", back_populates="learning_records")

    # 注意：因为 question_id 可为空，这里的关系在访问时需确保 question_id 存在
    question = relationship("Question", back_populates="learning_records")

    def __repr__(self):
        return f"<LearningRecord(id={self.id}, user_id={self.user_id}, source={self.source_type})>"
