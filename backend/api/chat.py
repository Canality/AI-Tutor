from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
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

        # questions.user_id 当前是 unique=True，这里采用“按用户更新/不存在则创建”
        question_stmt = select(Question).where(Question.user_id == current_user.id)
        question_result = await db.execute(question_stmt)
        question_record = question_result.scalars().first()

        if question_record is None:
            question_record = Question(
                user_id=current_user.id,
                content=question,
                question_type="image" if image_path else "text",
            )
            db.add(question_record)
        else:
            question_record.content = question
            question_record.question_type = "image" if image_path else "text"

        await db.commit()

        logger.info(
            f"question saved, user_id={current_user.id}, message_id={chat_message.id}, question_id={question_record.id}"
        )

        async def generate():
            async for chunk in tutor_service.process_question_stream(question, image_path):
                yield f"data: {chunk}\n\n"

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