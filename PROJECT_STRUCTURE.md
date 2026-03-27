# AI Tutor 项目代码结构文档

> 本文档记录 AI Tutor - 高中数学数列智能辅导系统 的代码结构，方便团队成员查阅和维护。
> 最后更新：2026-03-27

---

## 📁 项目根目录结构

```
AI Tutor/
├── backend/                    # 后端服务 (FastAPI)
├── frontend/                   # 前端应用 (Vue3)
├── knowledge_base/             # 知识库题目 (Markdown格式)
├── dataset/                    # 数据集文件 (JSON格式)
├── docs/                       # 项目文档
├── prompts/                    # Prompt模板
├── storage/                    # 存储目录
│   ├── chroma/                 # ChromaDB向量数据库
│   └── uploads/                # 用户上传文件
├── logs/                       # 日志文件
├── database/                   # 数据库脚本
├── README.md                   # 项目说明
├── SETUP.md                    # 部署指南
└── TASKS.md                    # 任务清单
```

---

## 🔧 后端目录 (backend/)

### 核心入口
| 文件 | 作用 |
|------|------|
| `main.py` | FastAPI应用主入口，注册所有路由和中间件 |
| `start.py` | 启动脚本，处理环境初始化和服务器启动 |
| `.env` | 环境变量配置文件（API密钥、数据库连接等） |
| `.env.example` | 环境变量模板 |
| `requirements.txt` | Python依赖包列表 |

### API接口层 (api/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | API模块初始化 |
| `chat.py` | Tutor对话接口，处理学生提问和AI回答 |
| `auth.py` | 用户认证接口，登录/注册/Token刷新 |
| `profile.py` | 学生画像接口，获取/更新学习档案 |
| `exercises.py` | 练习题推荐接口 |
| `records.py` | 学习记录接口，保存/查询学习历史 |
| `upload.py` | 文件上传接口，处理图片/文档上传 |
| `rag.py` | RAG系统API，提供检索和提示词生成接口 |
| `records_example.py` | 学习记录示例数据 |

### Agent系统 (agent/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | Agent模块初始化 |
| `instructor.py` | Instructor Agent - 解题辅导Agent，提供分步骤讲解 |
| `advisor.py` | Advisor Agent - 学习规划Agent，生成学习计划和推荐 |
| `prompt.py` | Prompt模板管理，加载和格式化系统提示词 |
| `tools.py` | Agent工具函数，供Agent调用的工具集 |

### RAG模块 (rag/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | RAG模块初始化 |
| `vector_db.py` | 向量数据库核心模块，封装ChromaDB操作 |
| `retriever.py` | 检索器，实现知识点和例题的向量检索 |
| `pipeline.py` | **RAG Pipeline**，完整检索增强生成流程 |
| `init_chroma_db.py` | 向量数据库初始化脚本，导入题目数据 |
| `add_mock_data.py` | 插入测试数据脚本 |
| `test_rag.py` | RAG系统测试脚本 |
| `storage/chroma/` | ChromaDB持久化存储目录 |

### 知识图谱 (kg/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | KG模块初始化 |
| `kg_builder.py` | 知识图谱构建器，从题目构建KG |
| `kg_query.py` | 知识图谱查询接口 |

### 多模态处理 (multimodal/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | 多模态模块初始化 |
| `image_parser.py` | 图片解析器，OCR识别图片中的数学题 |
| `file_parser.py` | 文件解析器，处理PDF/Word等文档 |
| `question_formatter.py` | 题目格式化，统一转换为标准格式 |

### 数据模型 (models/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | 模型模块初始化 |
| `user.py` | 用户模型，用户表结构定义 |
| `question.py` | 题目模型，题库表结构定义 |
| `record.py` | 学习记录模型 |
| `profile.py` | 学生画像模型 |
| `chat.py` | 对话记录模型 |

### 业务服务层 (services/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | 服务模块初始化 |
| `auth_service.py` | 认证服务，处理登录注册逻辑 |
| `tutor_service.py` | Tutor服务，调用Agent进行辅导 |
| `profile_service.py` | 画像服务，更新学生画像 |
| `recommendation_service.py` | 推荐服务，生成练习题推荐 |
| `record_service.py` | 记录服务，管理学习记录 |

### 数据库 (database/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | 数据库模块初始化 |
| `db.py` | 数据库连接配置，SQLAlchemy异步引擎 |
| `init_db.py` | 数据库初始化脚本，创建表结构 |

### 数据验证 (schemas/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | Schemas模块初始化 |
| `auth.py` | 认证相关数据验证模型 |
| `question.py` | 题目数据验证模型 |

### 工具函数 (utils/)
| 文件 | 作用 |
|------|------|
| `__init__.py` | 工具模块初始化 |
| `config.py` | 配置管理，读取环境变量和配置项 |
| `logger.py` | 日志工具，统一日志格式和输出 |
| `data_loader.py` | 数据加载器，加载JSON题库数据 |
| `siliconflow_vision.py` | 硅基流动视觉模型客户端 |
| `volc_engine.py` | 火山引擎API客户端 |

### 数据集 (dataset/)
| 文件 | 作用 |
|------|------|
| `DATASET_README.md` | 数据集说明文档 |
| `DATASET_SCHEMA.md` | 数据集结构规范 |
| `index.json` | 题目索引文件 |
| `member_E_questions.json` | 组员E整理的题目数据（P123-P144） |
| `member_E_questions_with_embedding.json` | 带向量嵌入的题目数据 |
| `question_template.json` | 题目数据模板 |
| `sequence_problems_template.json` | 数列题模板 |

---

## 🎨 前端目录 (frontend/)

### 核心文件
| 文件 | 作用 |
|------|------|
| `index.html` | HTML入口文件 |
| `main.js` | Vue应用入口，初始化Vue实例 |
| `App.vue` | 根组件 |
| `vite.config.js` | Vite构建配置 |
| `package.json` | npm依赖配置 |

### 页面组件 (pages/)
| 文件 | 作用 |
|------|------|
| `index.vue` | 首页/入口页面 |
| `LoginView.vue` | 登录页面 |
| `RegisterView.vue` | 注册页面 |
| `AiTutorView.vue` | AI辅导主页面，题目输入和解答展示 |
| `ProfileView.vue` | 学生画像页面 |
| `ExercisesView.vue` | 练习题页面 |
| `RecommendView.vue` | 推荐页面 |
| `main.html` | 备用主页面 |

### 组件 (components/)
| 文件 | 作用 |
|------|------|
| `QuestionInput.vue` | 题目输入组件，支持文本和图片 |
| `AnswerDisplay.vue` | 答案展示组件，渲染解题步骤 |
| `Navigation.vue` | 导航栏组件 |

### 路由 (router/)
| 文件 | 作用 |
|------|------|
| `index.js` | Vue Router配置，定义路由规则 |

### 服务层 (services/)
| 文件 | 作用 |
|------|------|
| `apiService.js` | API服务封装，统一处理HTTP请求 |
| `tutor-api.js` | Tutor相关API封装 |

### 样式 (assets/)
| 文件 | 作用 |
|------|------|
| `main.css` | 主样式文件 |
| `base.css` | 基础样式 |

---

## 📚 知识库 (knowledge_base/)

```
knowledge_base/
└── question/
    ├── member_A/           # 组员A负责的题目
    ├── member_C/           # 组员C负责的题目
    ├── member_D/           # 组员D负责的题目
    └── member_E/           # 组员E负责的题目 (P123-P144)
```

每个题目以Markdown文件存储，命名格式：`{页码}_{题型}{题号}_{类型}_{标题}.md`

---

## 🗄️ 存储目录 (storage/)

```
storage/
├── chroma/                 # ChromaDB向量数据库文件
│   ├── chroma.sqlite3      # SQLite主数据库
│   └── {uuid}/             # 向量集合存储目录
│       ├── data_level0.bin
│       ├── header.bin
│       ├── length.bin
│       └── link_lists.bin
└── uploads/                # 用户上传文件
    └── {uuid}.png          # 上传的图片文件
```

---

## 📝 文档目录 (docs/)

| 文件 | 作用 |
|------|------|
| `architecture.md` | 系统架构设计文档 |
| `plan.md` | 项目规划文档 |
| `team_assignment.md` | 团队分工文档 |
| `user_stories.md` | 用户故事文档 |
| `instructor_prompt_optimization.md` | Instructor Prompt优化记录 |
| `rag_system.md` | **RAG系统文档**，检索增强生成系统说明 |

---

## ⚙️ 配置说明

### 环境变量 (.env)

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `OPENAI_API_KEY` | 硅基流动API密钥 | sk-xxx |
| `OPENAI_API_BASE` | API基础URL | https://api.siliconflow.cn/v1 |
| `LLM_MODEL` | 主模型名称 | deepseek-ai/DeepSeek-R1 |
| `EMBEDDING_MODEL` | 向量模型 | BAAI/bge-large-zh-v1.5 |
| `CHROMA_PERSIST_DIR` | ChromaDB存储路径 | ./storage/chroma |
| `MYSQL_*` | MySQL数据库配置 | - |
| `REDIS_*` | Redis缓存配置 | - |

---

## 🔄 数据流说明

```
用户提问 → API层 → Tutor Service → Instructor Agent
                                      ↓
                              RAG检索 (ChromaDB)
                                      ↓
                              知识图谱查询 (KG)
                                      ↓
                              LLM生成回答
                                      ↓
                              返回给用户
```

---

## 📌 注意事项

1. **不要直接修改** `storage/chroma/` 下的文件，这些由ChromaDB自动管理
2. **知识库题目**以Markdown格式存储在 `knowledge_base/question/` 下
3. **数据集JSON**用于向量数据库初始化，位于 `backend/dataset/`
4. **环境变量**需要配置在 `backend/.env` 文件中

---

## 🚀 快速启动

```bash
# 启动后端
cd backend
python start.py

# 启动前端
cd frontend
npm run dev
```

或使用批处理文件：
```bash
start_backend.bat   # 启动后端
start_frontend.bat  # 启动前端
```
