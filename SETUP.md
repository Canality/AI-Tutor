# AI Tutor 项目快速启动指南

## 环境要求

- Python 3.9
- MySQL 8.0+
- Redis 6.0+

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd AI-Tutor-main
```

### 2. 创建虚拟环境（推荐）


```bash

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

在此之前要先更新pip


```bash
pip install pip-tools

pip-compile requirements.in

pip-sync requiremnets.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env`，并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下内容：

- MySQL 数据库连接信息
- Redis 连接信息
- OpenAI API Key（如需要）
- JWT Secret Key

### 5. 创建数据库

在 MySQL 中创建数据库：

```sql
CREATE DATABASE ai_tutor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. 初始化数据库表

```bash
cd backend
python -m backend.database.init_db
```

### 7. 启动后端服务

```bash
# 方式1：直接运行
cd backend
python -m backend.main

# 方式2：使用 uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. 访问服务

- API 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

## 项目结构说明

```
AI-Tutor-main/
├── backend/              # 后端代码
│   ├── agent/           # Agent 模块
│   ├── api/             # API 接口
│   ├── database/        # 数据库配置
│   ├── kg/              # 知识图谱
│   ├── models/          # 数据模型
│   ├── multimodal/      # 多模态处理
│   ├── rag/             # RAG 模块
│   ├── services/        # 业务服务
│   ├── utils/           # 工具类
│   └── main.py          # 应用入口
├── docs/                # 文档
├── frontend/            # 前端代码
├── dataset/             # 数据集
└── prompts/             # Prompt 模板
```

## 常用命令

```bash
# 初始化数据库
python -m backend.database.init_db

# 启动后端服务
uvicorn backend.main:app --reload

```

