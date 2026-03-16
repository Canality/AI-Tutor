# AI Tutor - 高中数学数列智能辅导系统 设计文档

## 文档信息
| 项目 | 内容 |
|------|------|
| 文档版本 | V1.0 |
| 适用系统 | AI Tutor - 高中数学数列智能辅导系统 |
| 核心技术栈 | Vue3 + FastAPI + MySQL + Chroma + LangChain + NetworkX |
| 文档目的 | 描述系统架构、技术选型、模块设计与实现方案 |

---

## 一、系统概述

### 1.1 项目背景
本项目旨在开发一个基于大语言模型（LLM）的 AI Tutor 系统，专门用于辅助高中生学习数学数列知识。系统采用多 Agent 协作架构，结合 RAG（检索增强生成）和知识图谱（KG）技术，提供智能、个性化的学习辅导服务。

### 1.2 系统目标
- 提供数学数列题目的智能分析与分步骤解题讲解
- 构建学生学习画像，实现个性化练习题推送
- 生成短期学习计划，帮助学生系统学习数列知识
- 支持多模态输入（文本、图片），提升用户体验

---

## 二、系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                         前端层 (Vue3)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  登录/注册  │  │  聊天界面   │  │  学习画像   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │  题目输入   │  │  练习推荐   │                         │
│  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      API 网关层 (FastAPI)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Auth    │  │  Chat    │  │  Profile │  │ Exercise│ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     业务逻辑层                             │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │    Instructor Agent  │  │     Advisor Agent    │    │
│  │  - 题目分析          │  │  - 学生画像生成      │    │
│  │  - 分步骤解题        │  │  - 练习题推荐        │    │
│  │  - 知识点关联        │  │  - 学习计划生成      │    │
│  └──────────────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   数据访问层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   RAG 模块   │  │  知识图谱    │  │  多模态解析  │  │
│  │  - 向量检索  │  │  - KG 查询   │  │  - 图片解析  │  │
│  │  - 文档检索  │  │  - 关系查询  │  │  - 文件解析  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                       数据存储层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │  MySQL   │  │  Chroma  │  │  Redis   │  │  文件   ││
│  │  关系型   │  │  向量库  │  │  缓存    │  │  存储   ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────┘
```

### 2.2 分层说明

#### 2.2.1 前端层
- **技术栈**：Vue3 + Axios + SSE
- **职责**：
  - 用户界面交互
  - 题目输入（文本/图片）
  - 解题步骤展示
  - 学习画像展示
  - 练习题列表展示

#### 2.2.2 API 网关层
- **技术栈**：FastAPI
- **职责**：
  - RESTful API 接口暴露
  - 请求路由与参数校验
  - 用户认证与授权
  - SSE 流式响应支持

#### 2.2.3 业务逻辑层
- **Instructor Agent**：题目分析、分步骤解题讲解
- **Advisor Agent**：学生画像生成、个性化练习推荐、学习计划生成

#### 2.2.4 数据访问层
- **RAG 模块**：向量数据库检索、相关题目/知识点召回
- **知识图谱模块**：知识点关系查询、题目-知识点关联
- **多模态解析**：图片题目解析、PDF/文档解析

#### 2.2.5 数据存储层
- **MySQL**：用户数据、题目数据、学习记录
- **Chroma**：向量数据库，存储题目和知识点向量
- **Redis**：缓存、Session 管理
- **文件存储**：用户上传图片、文档

---

## 三、功能模块设计

### 3.1 模块划分

| 模块名称 | 核心功能 | 负责人 |
|----------|----------|--------|
| 基础框架模块 | 项目初始化、数据库配置、基础工具类 | 成员B |
| 用户认证模块 | 登录、注册、权限管理 | 成员C |
| Instructor Agent 模块 | 题目分析、分步骤解题、RAG 集成 | 成员D |
| Advisor Agent 模块 | 学习画像、练习推荐、学习计划 | 成员E |
| 前端模块 | 用户界面、交互逻辑、API 对接 | 成员A |

### 3.2 核心模块详细设计

#### 3.2.1 基础框架模块
**职责**：
- 项目目录结构搭建
- 数据库配置与连接（MySQL、Redis）
- 配置管理（环境变量、配置文件）
- 日志系统
- 基础工具类

**核心文件**：
- `backend/main.py` - FastAPI 应用入口
- `backend/database/db.py` - 数据库连接配置
- `backend/database/init_db.py` - 数据库初始化
- `backend/utils/config.py` - 配置管理
- `backend/utils/logger.py` - 日志系统

#### 3.2.2 用户认证模块
**职责**：
- 用户注册/登录
- JWT Token 生成与验证
- 用户信息管理

**核心文件**：
- `backend/api/auth.py` - 认证接口
- `backend/services/auth_service.py` - 认证业务逻辑
- `backend/models/user.py` - 用户数据模型

#### 3.2.3 Instructor Agent 模块
**职责**：
- 题目理解与分析
- 分步骤解题讲解生成
- RAG 检索相关题目/知识点
- 知识图谱查询关联

**核心文件**：
- `backend/agent/instructor.py` - Instructor Agent 实现
- `backend/rag/vector_db.py` - 向量数据库操作
- `backend/rag/retriever.py` - 检索逻辑
- `backend/kg/kg_query.py` - 知识图谱查询

#### 3.2.4 Advisor Agent 模块
**职责**：
- 学生学习画像生成与更新
- 个性化练习题推荐
- 短期学习计划生成
- 错题分析

**核心文件**：
- `backend/agent/advisor.py` - Advisor Agent 实现
- `backend/services/profile_service.py` - 画像服务
- `backend/services/recommendation_service.py` - 推荐服务
- `backend/models/profile.py` - 学生画像模型

#### 3.2.5 前端模块
**职责**：
- 用户界面实现
- 题目输入（文本/图片）
- 解题步骤展示
- 学习画像展示
- API 对接

**核心文件**：
- `frontend/pages/login.vue` - 登录页
- `frontend/pages/chat.vue` - 聊天/解题页
- `frontend/pages/profile.vue` - 学习画像页
- `frontend/components/QuestionInput.vue` - 题目输入组件
- `frontend/components/AnswerDisplay.vue` - 解题步骤展示组件
- `frontend/services/api.js` - API 封装

---

## 四、数据库设计

### 4.1 MySQL 数据表设计

#### 4.1.1 用户表 (users)
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INT | 用户ID | PRIMARY KEY, AUTO_INCREMENT |
| username | VARCHAR(50) | 用户名 | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | 密码哈希 | NOT NULL |
| email | VARCHAR(100) | 邮箱 | UNIQUE |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP ON UPDATE |

#### 4.1.2 题目表 (questions)
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INT | 题目ID | PRIMARY KEY, AUTO_INCREMENT |
| content | TEXT | 题目内容 | NOT NULL |
| answer | TEXT | 标准答案 | |
| difficulty | INT | 难度(1-5) | |
| knowledge_points | JSON | 关联知识点 | |
| problem_type | VARCHAR(50) | 题目类型 | |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

#### 4.1.3 学习记录表 (learning_records)
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INT | 记录ID | PRIMARY KEY, AUTO_INCREMENT |
| user_id | INT | 用户ID | FOREIGN KEY → users.id |
| question_id | INT | 题目ID | FOREIGN KEY → questions.id |
| is_correct | BOOLEAN | 是否正确 | |
| user_answer | TEXT | 用户答案 | |
| created_at | DATETIME | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

#### 4.1.4 学生画图表 (user_profiles)
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INT | 画像ID | PRIMARY KEY, AUTO_INCREMENT |
| user_id | INT | 用户ID | FOREIGN KEY → users.id, UNIQUE |
| knowledge_mastery | JSON | 知识点掌握度 | |
| weak_points | JSON | 薄弱知识点 | |
| total_questions | INT | 总答题数 | DEFAULT 0 |
| correct_count | INT | 正确数 | DEFAULT 0 |
| updated_at | DATETIME | 更新时间 | DEFAULT CURRENT_TIMESTAMP ON UPDATE |

### 4.2 向量数据库设计 (Chroma)
- **Collection 名称**：sequence_questions
- **存储内容**：题目内容向量化
- **Metadata**：题目ID、难度、知识点、题目类型

### 4.3 知识图谱设计 (NetworkX)
- **节点类型**：知识点、题目、解题方法
- **边类型**：
  - 题目 → 知识点（关联）
  - 知识点 → 知识点（前置/后继）
  - 题目 → 解题方法（使用）

---

## 五、API 接口设计

### 5.1 认证接口 (/api/auth)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /register | 用户注册 |
| POST | /login | 用户登录 |
| GET | /me | 获取当前用户信息 |

### 5.2 聊天接口 (/api/chat)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /ask | 发送问题，获取解答 |
| POST | /ask-stream | 流式获取解答 (SSE) |

### 5.3 学生画像接口 (/api/profile)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 获取学生画像 |
| PUT | / | 更新学生画像 |

### 5.4 练习题接口 (/api/exercises)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /recommend | 获取推荐练习题 |
| GET | /plan | 获取学习计划 |

### 5.5 上传接口 (/api/upload)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /image | 上传图片题目 |

---

## 六、技术选型说明

| 技术组件 | 选型 | 说明 |
|----------|------|------|
| 后端框架 | FastAPI | 异步、高性能、自动生成 API 文档 |
| 前端框架 | Vue3 | 组合式 API、响应式、生态完善 |
| 数据库 | MySQL | 关系型数据库，成熟稳定 |
| 向量数据库 | Chroma | 轻量级、易用、LangChain 集成好 |
| 缓存 | Redis | 高性能缓存、会话管理 |
| LLM 框架 | LangChain | Agent 编排、RAG 支持 |
| 知识图谱 | NetworkX | Python 图计算库，易用 |
| OCR | 待定 | 图片题目识别 |

---

## 七、开发规范

### 7.1 代码规范
- **后端**：遵循 PEP 8 规范
- **前端**：遵循 ESLint + Prettier 规范
- **Git 提交**：`[模块名] 功能描述`

### 7.2 协作规范
- 前后端并行开发，基于 API 文档对接
- 每个功能模块独立开发和测试
- 关键代码必须进行代码评审
