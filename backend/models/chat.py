from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base
import enum


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class RoleType(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_name = Column(String(255), nullable=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active", index=True)
    total_messages = Column(Integer, default=0)

    user = relationship("User", backref="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(Enum(RoleType), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    image_path = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_solution = Column(Boolean, default=False)

    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User")
    solution_steps = relationship("SolutionStep", back_populates="message", cascade="all, delete-orphan")


class SolutionStep(Base):
    __tablename__ = "solution_steps"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False, index=True)
    step_content = Column(Text, nullable=False)
    knowledge_point = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("ChatMessage", back_populates="solution_steps")


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=True, index=True)
    level = Column(Integer, default=1, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("KnowledgePoint", remote_side=[id], backref="children")
    # 关键修改：将 backref="knowledge_points" 改为 backref="related_knowledge_points"
    # 新名称不会和 Question 模型中的 knowledge_points (JSON字段) 冲突
    questions = relationship("Question", secondary="question_knowledge_points", backref="related_knowledge_points")
    user_mastery = relationship("UserKnowledgeMastery", back_populates="knowledge_point")


class QuestionKnowledgePoint(Base):
    __tablename__ = "question_knowledge_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserKnowledgeMastery(Base):
    __tablename__ = "user_knowledge_mastery"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False, index=True)
    mastery_level = Column(Integer, default=0, index=True)
    practice_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    # V3 扩展字段(BKT 参数)
    p_guess = Column(Float, default=0.2)
    p_slip = Column(Float, default=0.1)
    p_known = Column(Float, default=0.5)
    consecutive_correct = Column(Integer, default=0)
    consecutive_wrong = Column(Integer, default=0)


    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    user = relationship("User", backref="knowledge_mastery")
    knowledge_point = relationship("KnowledgePoint", back_populates="user_mastery")