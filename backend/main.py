import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.config import settings
from utils.logger import logger
from database.db import init_db
from api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")

    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    os.makedirs(os.path.join(project_root, settings.log_dir), exist_ok=True)
    os.makedirs(os.path.join(project_root, settings.upload_dir), exist_ok=True)
    os.makedirs(os.path.join(project_root, settings.chroma_persist_dir), exist_ok=True)
    os.makedirs(os.path.join(project_root, settings.kg_persist_dir), exist_ok=True)

    await init_db()

    logger.info(f"{settings.app_name} started successfully!")
    yield
    logger.info(f"{settings.app_name} shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Tutor - 高中数学数列智能辅导系统",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Tutor!",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
