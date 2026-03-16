from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database.db import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    content = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    difficulty = Column(Integer, nullable=True)
    knowledge_points = Column(JSON, nullable=True)
    problem_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    learning_records = relationship("LearningRecord", back_populates="question")
