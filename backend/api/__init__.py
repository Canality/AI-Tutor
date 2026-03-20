from fastapi import APIRouter
from api import auth, chat, exercises, profile, upload, records

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(exercises.router, tags=["exercises"])
api_router.include_router(profile.router, tags=["profile"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(records.router, tags=["records"])
