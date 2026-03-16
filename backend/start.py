#!/usr/bin/env python3
import os
import asyncio
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import settings
from utils.logger import logger
from database.db import init_db


def check_env_file():
    """检查环境变量文件"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 检查 backend 目录下的 .env 文件
    env_file = os.path.join(project_root, "backend", ".env")
    env_example = os.path.join(project_root, ".env.example")
    
    if not os.path.exists(env_file):
        logger.warning(f"未找到 {env_file} 文件，将使用默认配置")
        # 复制示例文件
        if os.path.exists(env_example):
            logger.info(f"从 {env_example} 复制创建 {env_file}")
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已创建 {env_file} 文件，请根据实际情况修改配置")
        else:
            logger.error(f"未找到 {env_example} 文件，请手动创建 {env_file} 文件")
            return False
    return True


def check_directories():
    """检查必要的目录"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    directories = [
        os.path.join(project_root, settings.log_dir),
        os.path.join(project_root, settings.upload_dir),
        os.path.join(project_root, settings.chroma_persist_dir),
        os.path.join(project_root, settings.kg_persist_dir)
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"确保目录存在: {directory}")


async def initialize_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        await init_db()
        logger.info("数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def start_server():
    """启动 FastAPI 服务器"""
    import uvicorn
    
    logger.info(f"启动 {settings.app_name} v{settings.app_version}...")
    logger.info(f"服务地址: http://{settings.host}:{settings.port}")
    logger.info(f"API 文档: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


async def main():
    """主函数"""
    logger.info("=====================================")
    logger.info(f"{settings.app_name} 启动脚本")
    logger.info(f"版本: {settings.app_version}")
    logger.info("=====================================")
    
    # 检查环境文件
    if not check_env_file():
        logger.error("环境配置检查失败，退出启动")
        sys.exit(1)
    
    # 检查目录
    check_directories()
    
    # 初始化数据库
    if not await initialize_database():
        logger.error("数据库初始化失败，退出启动")
        sys.exit(1)
    
    # 启动服务器
    logger.info("=====================================")
    logger.info("所有初始化步骤完成，启动服务器...")
    logger.info("=====================================")
    
    # 启动服务器（非异步）
    start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务已手动停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
