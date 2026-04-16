from fastapi import APIRouter
from api import auth, chat, exercises, profile, upload, records, rag, questions, learning_tools, advisor, cognitive_diagnosis


api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(exercises.router, tags=["exercises"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(records.router, tags=["records"])
api_router.include_router(rag.router, tags=["rag"])
api_router.include_router(questions.router, tags=["questions"])
api_router.include_router(learning_tools.router, tags=["learning-tools"])
api_router.include_router(advisor.router, tags=["advisor"])
api_router.include_router(cognitive_diagnosis.router)

