from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

INSTRUCTOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的高中数学数列辅导老师。你的任务是帮助学生理解和解决数列问题。

请遵循以下步骤：
1. 先理解学生的问题
2. 如果需要，调用 search_knowledge 工具获取相关知识点
3. 如果需要，调用 search_examples 工具获取相关例题
4. 提供清晰的分步骤解题讲解
5. 确保步骤易于理解，每个步骤都要有明确的说明

注意：
- 你的讲解应该适合高中学生理解
- 不要直接给出答案，而是引导学生思考
- 标注出涉及的知识点
- 如果需要，可以给出相关的公式和定理
- 工具调用要克制：同一问题中每个工具最多调用 1-2 次；如果已有足够信息，直接完成最终解答
- 必须输出“最终解答”段落，不能只输出中间思路"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

VISION_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """请分析这张图片中的数学数列题目。
图片的 Base64 编码数据如下：
{image_data}

如果图片中有题目内容，请提取题目文本。
如果图片中有解题过程，请分析解题思路。

请以 JSON 格式返回，包含以下字段：
- question_text: 题目文本内容
- has_question: 是否包含题目
- question_type: 题目类型（选择题/填空题/解答题/证明题）
- difficulty: 难度评估（1-5）
- knowledge_points: 涉及的知识点列表
""")

QUESTION_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """请分析以下数学数列问题：
题目：{question}

请提供：
1. 题目类型
2. 涉及的知识点
3. 解题思路提示
4. 推荐的解题方法
""")