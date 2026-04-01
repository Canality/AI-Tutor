from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage
import os
import uuid

from database.db import get_db
from models.chat import ChatSession, ChatMessage, MessageType, RoleType
from models.question import Question
from models.user import User
from services.auth_service import get_current_user
from services.tutor_service import tutor_service
from utils.config import settings
from utils.logger import logger

router = APIRouter(prefix="/chat")


async def save_uploaded_file(upload_file: UploadFile) -> str:
    """save uploaded file to local storage and return the file path"""
    os.makedirs(settings.upload_dir, exist_ok=True)

    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)

    logger.info(f"file saved: {file_path}")
    return file_path


@router.post("/ask-stream")
async def ask_stream(
    question: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        image_path = None

        if image:
            image_path = await save_uploaded_file(image)

        session_stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id, ChatSession.status == "active")
            .order_by(ChatSession.start_time.desc())
        )
        session_result = await db.execute(session_stmt)
        chat_session = session_result.scalars().first()

        if chat_session is None:
            chat_session = ChatSession(
                user_id=current_user.id,
                session_name=(question[:50] if question else "新会话"),
                status="active",
                total_messages=0,
            )
            db.add(chat_session)
            await db.flush()

        chat_message = ChatMessage(
            session_id=chat_session.id,
            user_id=current_user.id,
            role=RoleType.USER,
            content=question,
            message_type=MessageType.IMAGE if image_path else MessageType.TEXT,
            image_path=image_path,
        )
        db.add(chat_message)
        chat_session.total_messages = (chat_session.total_messages or 0) + 1

        question_record = Question(
            user_id=current_user.id,
            content=question,
            question_type="image" if image_path else "text",
        )
        db.add(question_record)

        await db.commit()

        logger.info(
            f"question saved, user_id={current_user.id}, message_id={chat_message.id}, question_id={question_record.id}"
        )

        # 获取历史消息作为上下文
        history_stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(10)  # 获取最近10条消息
        )
        history_result = await db.execute(history_stmt)
        history_messages = history_result.scalars().all()
        
        # 转换为 LangChain 消息格式（排除当前这条用户消息）
        chat_history: List = []
        for msg in reversed(history_messages):  # 反转回正序
            if msg.id == chat_message.id:  # 跳过刚添加的当前消息
                continue
            if msg.role == RoleType.USER:
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == RoleType.ASSISTANT:
                chat_history.append(AIMessage(content=msg.content))
        
        logger.info(f"Loaded {len(chat_history)} history messages for context")

        async def generate():
            def _sse_event(data: str):
                safe_data = (data or "").replace("\r\n", "\n").replace("\r", "\n")
                for line in safe_data.split("\n"):
                    yield f"data: {line}\n"
                yield "\n"

            full_response = ""
            try:
                async for chunk in tutor_service.process_question_stream(question, image_path, chat_history):
                    full_response += chunk
                    for line in _sse_event(chunk):
                        yield line

                for line in _sse_event("[DONE]"):
                    yield line
            finally:
                # 保存 AI 回复到数据库（即使中途中断也尽量保存已生成内容）
                if full_response:
                    ai_message = ChatMessage(
                        session_id=chat_session.id,
                        user_id=current_user.id,
                        role=RoleType.ASSISTANT,
                        content=full_response,
                        message_type=MessageType.TEXT,
                    )
                    db.add(ai_message)
                    chat_session.total_messages += 1
                    await db.commit()
                    logger.info(f"AI response saved, session_id={chat_session.id}")

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Tutor service error: {e}")
        raise HTTPException(status_code=500, detail="Tutor service error")
