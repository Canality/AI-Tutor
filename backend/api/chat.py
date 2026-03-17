from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import os
import uuid
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
):
    try:
        image_path = None

        if image:
            image_path = await save_uploaded_file(image)
        
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