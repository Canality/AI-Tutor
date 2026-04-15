from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database.db import Base


class UserAbilityHistory(Base):
    __tablename__ = "user_ability_history"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    theta = Column(Float, nullable=False)
    theta_se = Column(Float, nullable=True)
    theta_ci_lower = Column(Float, nullable=True)
    theta_ci_upper = Column(Float, nullable=True)
    avg_mastery = Column(Float, nullable=True)
    weak_kp_count = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="ability_history")

    __table_args__ = (
        Index("idx_user_time", "user_id", "recorded_at"),
    )


class MistakeBook(Base):
    __tablename__ = "mistake_book"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    error_count = Column(Integer, default=1)
    first_error_at = Column(DateTime(timezone=True), server_default=func.now())
    last_error_at = Column(DateTime(timezone=True), server_default=func.now())
    mastered = Column(Boolean, default=False, index=True)
    mastered_at = Column(DateTime(timezone=True), nullable=True)
    review_count = Column(Integer, default=0)
    last_review_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="mistake_books")
    question = relationship("Question", lazy="joined")


    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uk_user_question"),
        Index("idx_user_mastered", "user_id", "mastered"),
        Index("idx_next_review", "user_id", "next_review_at"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    folder_name = Column(String(50), default="默认收藏夹", nullable=False)
    note = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favorites")
    question = relationship("Question", lazy="joined")


    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uk_user_question"),
        Index("idx_user_folder", "user_id", "folder_name"),
    )


class UserInteractionLog(Base):
    __tablename__ = "user_interaction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    interaction_type = Column(String(50), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    knowledge_points = Column(JSON, nullable=True)
    difficulty = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    interaction_metadata = Column("metadata", JSON, nullable=True)

    sentiment_tag = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="interaction_logs")
    question = relationship("Question")

    __table_args__ = (
        Index("idx_user_time", "user_id", "created_at"),
        Index("idx_session", "session_id"),
    )
