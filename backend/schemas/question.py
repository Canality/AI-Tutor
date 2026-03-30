"""
题目相关的 Pydantic Schema 定义

本模块定义了题目数据的校验模型，包括：
- CustomQuestionData: 用户上传题目的数据结构
- CustomQuestionPayload: API 层接收的用户上传题目数据
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomQuestionData(BaseModel):
    """
    自定义题目数据模型 - 用于存储在 learning_records.custom_question_data 中

    此模型复刻了 questions 表的核心字段结构，用于存储用户上传的题目。
    当 source_type = 'uploaded' 时，此模型的数据会被序列化为 JSON 存储。

    【字段映射关系】
    - content          -> questions.content
    - standard_answer  -> questions.standard_answer
    - difficulty       -> questions.difficulty
    - question_type    -> questions.question_type
    - knowledge_points -> questions.knowledge_points
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="题目内容文本，必填",
        examples=["解方程: 2x + 5 = 13"]
    )

    standard_answer: Optional[str] = Field(
        None,
        max_length=5000,
        description="标准答案，可选",
        examples=["x = 4"]
    )

    difficulty: int = Field(
        default=2,
        ge=1,
        le=5,
        description="难度等级: 1-简单, 2-中等, 3-较难, 4-困难, 5-极难",
        examples=[2]
    )

    question_type: Literal[
        "single_choice",      # 单选题
        "multiple_choice",    # 多选题
        "fill_blank",         # 填空题
        "short_answer",       # 简答题
        "essay",              # 论述题
        "calculation",        # 计算题
        "other"               # 其他类型
    ] = Field(
        default="short_answer",
        description="题目类型",
        examples=["short_answer"]
    )

    knowledge_points: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="知识点标签列表",
        examples=[["方程", "一元一次方程"]]
    )

    @field_validator('knowledge_points')
    @classmethod
    def validate_knowledge_points(cls, v: List[str]) -> List[str]:
        """验证知识点标签不为空字符串"""
        if v is None:
            return []
        # 过滤空字符串并去重
        cleaned = list(dict.fromkeys([kp.strip() for kp in v if kp and kp.strip()]))
        return cleaned

    class Config:
        """Pydantic V2 配置"""
        json_schema_extra = {
            "example": {
                "content": "解方程: 2x + 5 = 13",
                "standard_answer": "x = 4",
                "difficulty": 2,
                "question_type": "short_answer",
                "knowledge_points": ["方程", "一元一次方程"]
            }
        }


class CustomQuestionPayload(BaseModel):
    """
    用户上传题目的 API 请求载荷模型

    用于接收用户上传的题目数据，在 API 层进行严格校验。
    校验通过后，会转换为 CustomQuestionData 存储到数据库。

    【使用场景】
    - POST /api/records/upload - 用户上传题目并作答
    - POST /api/questions/upload - 仅上传题目
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="题目内容文本，必填",
        examples=["解方程: 2x + 5 = 13"]
    )

    standard_answer: Optional[str] = Field(
        None,
        max_length=5000,
        description="标准答案，可选。如果不提供，AI 将自动评估答案",
        examples=["x = 4"]
    )

    difficulty: int = Field(
        default=2,
        ge=1,
        le=5,
        description="难度等级: 1-简单, 2-中等, 3-较难, 4-困难, 5-极难",
        examples=[2]
    )

    question_type: Literal[
        "single_choice",
        "multiple_choice",
        "fill_blank",
        "short_answer",
        "essay",
        "calculation",
        "other"
    ] = Field(
        default="short_answer",
        description="题目类型",
        examples=["short_answer"]
    )

    knowledge_points: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="知识点标签列表，用于个性化推荐",
        examples=[["方程", "一元一次方程"]]
    )

    user_answer: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="用户的答案",
        examples=["x = 4"]
    )

    @field_validator('knowledge_points')
    @classmethod
    def validate_knowledge_points(cls, v: List[str]) -> List[str]:
        """验证知识点标签：去重、去空字符串、限制数量"""
        if v is None:
            return []
        # 过滤空字符串并去重，保持顺序
        cleaned = list(dict.fromkeys([kp.strip() for kp in v if kp and kp.strip()]))
        # 限制最多 20 个知识点
        return cleaned[:20]

    @field_validator('content', 'user_answer')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """去除首尾空白字符"""
        if v is None:
            return v
        return v.strip()

    def to_custom_question_data(self) -> CustomQuestionData:
        """
        转换为 CustomQuestionData 模型（去除 user_answer）

        用于将 API 接收的数据转换为数据库存储格式。
        user_answer 字段会单独存储到 learning_records.user_answer
        """
        return CustomQuestionData(
            content=self.content,
            standard_answer=self.standard_answer,
            difficulty=self.difficulty,
            question_type=self.question_type,
            knowledge_points=self.knowledge_points
        )

    class Config:
        """Pydantic V2 配置"""
        json_schema_extra = {
            "example": {
                "content": "解方程: 2x + 5 = 13",
                "standard_answer": "x = 4",
                "difficulty": 2,
                "question_type": "short_answer",
                "knowledge_points": ["方程", "一元一次方程"],
                "user_answer": "x = 4"
            }
        }


class QuestionResponse(BaseModel):
    """
    题目响应模型

    用于统一返回题目数据，无论来源是系统题库还是用户上传。
    """
    id: Optional[int] = Field(
        None,
        description="题目 ID，系统题库题有此字段，用户上传题为 null"
    )
    content: str = Field(..., description="题目内容")
    standard_answer: Optional[str] = Field(None, description="标准答案")
    difficulty: int = Field(default=2, description="难度等级")
    question_type: str = Field(default="short_answer", description="题目类型")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点")
    source_type: str = Field(..., description="来源类型: uploaded/recommended/practice")

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="题目内容文本"
    )
    standard_answer: Optional[str] = Field(
        None,
        max_length=5000,
        description="标准答案"
    )
    difficulty: int = Field(
        default=2,
        ge=1,
        le=5,
        description="难度等级"
    )
    question_type: Literal[
        "single_choice",
        "multiple_choice",
        "fill_blank",
        "short_answer",
        "essay",
        "calculation",
        "other",
        "text",
        "image",
    ] = Field(
        default="short_answer",
        description="题目类型"
    )
    knowledge_points: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="知识点列表"
    )

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return v.strip()

    @field_validator("knowledge_points")
    @classmethod
    def normalize_knowledge_points(cls, v: List[str]) -> List[str]:
        if v is None:
            return []
        return list(dict.fromkeys([kp.strip() for kp in v if kp and kp.strip()]))[:20]


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    content: Optional[str] = Field(
        None,
        min_length=1,
        max_length=10000,
        description="题目内容文本"
    )
    standard_answer: Optional[str] = Field(
        None,
        max_length=5000,
        description="标准答案"
    )
    difficulty: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="难度等级"
    )
    question_type: Optional[Literal[
        "single_choice",
        "multiple_choice",
        "fill_blank",
        "short_answer",
        "essay",
        "calculation",
        "other",
        "text",
        "image",
    ]] = Field(
        None,
        description="题目类型"
    )
    knowledge_points: Optional[List[str]] = Field(
        None,
        max_length=20,
        description="知识点列表"
    )

    @field_validator("content")
    @classmethod
    def strip_optional_content(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip()

    @field_validator("knowledge_points")
    @classmethod
    def normalize_optional_knowledge_points(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        return list(dict.fromkeys([kp.strip() for kp in v if kp and kp.strip()]))[:20]


class QuestionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    content: str
    standard_answer: Optional[str]
    difficulty: int
    question_type: Optional[str]
    knowledge_points: List[str] = Field(default_factory=list)
    created_at: Optional[datetime]
