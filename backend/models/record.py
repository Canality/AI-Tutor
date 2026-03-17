from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database.db import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    # --- 基础主键 ---
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # --- 核心修改点 1: 题目关联 (允许为空) ---
    # 如果是系统推荐题，这里有值；如果是用户上传题，这里为 NULL
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)

    # --- 核心修改点 2: 来源标识 ---
    # 枚举值示例: 'uploaded' (用户上传), 'recommended' (系统推荐), 'practice' (随机练习)
    source_type = Column(String(50), nullable=False, default='recommended', index=True)

    # --- 核心修改点 3: 自定义题目数据存储 (针对上传题) ---
    # 当 question_id 为 NULL 时，这里存储用户上传的题目详情
    # 结构示例: {"question_text": "...", "standard_answer": "...", "analysis": "...", "tags": [...]}
    custom_question_data = Column(JSON, nullable=True)

    # --- 答题情况 ---
    is_correct = Column(Boolean, nullable=True)  # 用户上传的题目可能暂时没有标准答案，允许为空
    user_answer = Column(Text, nullable=True)  # 学生的作答

    # AI 反馈或解析 (无论哪种来源，都可以存储 AI 生成的解析)
    ai_feedback = Column(Text, nullable=True)

    # --- 推荐上下文 (针对推荐题) ---
    # 记录这次做题是属于哪一次推荐会话，用于分析推荐算法效果
    recommendation_session_id = Column(String(100), nullable=True, index=True)

    # --- 时间戳 ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- 关系定义 ---
    # back_populates 需要在 User 模型中也对应添加
    user = relationship("User", back_populates="learning_records")

    # 注意：因为 question_id 可为空，这里的关系在访问时需确保 question_id 存在
    question = relationship("Question", back_populates="learning_records")

    def __repr__(self):
        return f"<LearningRecord(id={self.id}, user_id={self.user_id}, source={self.source_type})>"
