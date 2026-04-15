from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey, Float, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    knowledge_mastery = Column(JSON, nullable=True)
    weak_points = Column(JSON, nullable=True)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    # V3 扩展字段
    theta_se = Column(Float, nullable=True)
    theta_ci_lower = Column(Float, nullable=True)
    theta_ci_upper = Column(Float, nullable=True)
    avg_mastery = Column(Float, nullable=True)
    weak_kp_count = Column(Integer, default=0)
    learning_style = Column(String(20), nullable=True)
    mastery_strategy = Column(String(20), default='simple')

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="profile")
