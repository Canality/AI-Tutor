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
    """保存上传的文件。"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)
    
    logger.info(f"文件已保存: {file_path}")
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
            """异步生成器函数，用于流式处理问题并返回结果。
            
            该函数使用 tutor_service.process_question_stream 处理用户问题和可选的图片，
            并通过 yield 语句逐个返回处理结果的 chunks，实现流式响应。
            
            注意：该函数使用了外部作用域的 question 和 image_path 变量。
            
            Yields:
                str: 处理结果的文本块，用于流式响应
            """
            async for chunk in tutor_service.process_question_stream(question, image_path):
                yield chunk
            
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"处理请求时发生错误: {e}")
        raise HTTPException(status_code=500, detail="处理请求时发生错误")