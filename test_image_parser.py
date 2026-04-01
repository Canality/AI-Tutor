# 图片解析功能测试脚本
# 用于测试后端图片解析功能是否正常工作

import asyncio
import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from multimodal.image_parser import image_parser
from utils.siliconflow_vision import siliconflow_vision_client
from utils.config import settings
from utils.logger import logger
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

async def test_vision_client():
    """测试视觉模型客户端"""
    print("=" * 50)
    print("测试1: 视觉模型客户端初始化")
    print("=" * 50)
    
    print(f"API Key: {settings.openai_api_key[:20]}..." if settings.openai_api_key else "未配置")
    print(f"Vision Model: {settings.vision_model}")
    print(f"API Base: {settings.openai_api_base}")
    
    if not siliconflow_vision_client.client:
        print("❌ 视觉模型客户端未初始化 - API Key 可能缺失")
        return False
    
    print("✅ 视觉模型客户端初始化成功")
    return True

async def test_image_parser():
    """测试图片解析器"""
    print("\n" + "=" * 50)
    print("测试2: 图片解析功能")
    print("=" * 50)
    
    # 查找 uploads 目录中的图片
    uploads_dir = settings.upload_dir
    print(f"Uploads 目录: {uploads_dir}")
    
    if not os.path.exists(uploads_dir):
        print(f"❌ Uploads 目录不存在: {uploads_dir}")
        return False
    
    # 列出所有图片文件
    image_files = [f for f in os.listdir(uploads_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    
    if not image_files:
        print("❌ Uploads 目录中没有图片文件")
        return False
    
    print(f"找到 {len(image_files)} 个图片文件: {image_files}")
    
    # 测试第一个图片
    test_image = os.path.join(uploads_dir, image_files[0])
    print(f"\n测试图片: {test_image}")
    
    result = await image_parser.parse_image(test_image)
    
    if not result:
        print("❌ 图片解析返回 None")
        return False
    
    print(f"\n解析结果:")
    print(f"  success: {result.get('success')}")
    print(f"  has_question: {result.get('has_question')}")
    print(f"  error: {result.get('error', '无')}")
    print(f"  question_text: {result.get('question_text', '')[:200]}...")
    
    if result.get('success') and result.get('has_question'):
        print("\n✅ 图片解析成功！")
        return True
    else:
        print("\n⚠️ 图片解析完成但未识别到题目")
        return False

async def main():
    print("AI Tutor 图片解析功能测试")
    print("=" * 50)
    
    # 测试1: 客户端初始化
    client_ok = await test_vision_client()
    
    if not client_ok:
        print("\n❌ 视觉模型客户端初始化失败，请检查:")
        print("  1. .env 文件中的 OPENAI_API_KEY 是否配置正确")
        print("  2. VISION_MODEL 是否配置正确")
        return
    
    # 测试2: 图片解析
    parser_ok = await test_image_parser()
    
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"视觉模型客户端: {'✅ 通过' if client_ok else '❌ 失败'}")
    print(f"图片解析功能: {'✅ 通过' if parser_ok else '⚠️ 未完成'}")

if __name__ == "__main__":
    asyncio.run(main())
