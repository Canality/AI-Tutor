@echo off
chcp 65001 >nul
echo ==========================================
echo    AI Tutor 安装包制作工具
echo ==========================================
echo.

set "PROJECT_DIR=%~dp0"
set "PACKAGE_NAME=AI-Tutor-安装包"
set "PACKAGE_DIR=%PROJECT_DIR%%PACKAGE_NAME%"
set "ZIP_NAME=AI-Tutor-计算机设计大赛.zip"

echo [1/5] 清理旧文件...
if exist "%PACKAGE_DIR%" rd /s /q "%PACKAGE_DIR%"
if exist "%ZIP_NAME%" del /f /q "%ZIP_NAME%"

echo [2/5] 创建安装包目录...
mkdir "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%\backend"
mkdir "%PACKAGE_DIR%\frontend"
mkdir "%PACKAGE_DIR%\storage"
mkdir "%PACKAGE_DIR%\docs"

echo [3/5] 复制项目文件...

REM 复制后端代码（排除不必要的文件）
xcopy /s /e /i /y /q "backend\agent" "%PACKAGE_DIR%\backend\agent\" >nul
xcopy /s /e /i /y /q "backend\api" "%PACKAGE_DIR%\backend\api\" >nul
xcopy /s /e /i /y /q "backend\database" "%PACKAGE_DIR%\backend\database\" >nul
xcopy /s /e /i /y /q "backend\kg" "%PACKAGE_DIR%\backend\kg\" >nul
xcopy /s /e /i /y /q "backend\multimodal" "%PACKAGE_DIR%\backend\multimodal\" >nul
xcopy /s /e /i /y /q "backend\rag" "%PACKAGE_DIR%\backend\rag\" >nul
xcopy /s /e /i /y /q "backend\services" "%PACKAGE_DIR%\backend\services\" >nul
xcopy /s /e /i /y /q "backend\utils" "%PACKAGE_DIR%\backend\utils\" >nul
copy /y "backend\main.py" "%PACKAGE_DIR%\backend\" >nul
copy /y "backend\start.py" "%PACKAGE_DIR%\backend\" >nul
copy /y "backend\requirements.txt" "%PACKAGE_DIR%\backend\" >nul
copy /y "backend\.env" "%PACKAGE_DIR%\backend\.env.example" >nul

REM 复制前端代码
xcopy /s /e /i /y /q "frontend\src" "%PACKAGE_DIR%\frontend\src\" >nul
xcopy /s /e /i /y /q "frontend\public" "%PACKAGE_DIR%\frontend\public\" >nul
copy /y "frontend\package.json" "%PACKAGE_DIR%\frontend\" >nul
copy /y "frontend\vite.config.js" "%PACKAGE_DIR%\frontend\" >nul
copy /y "frontend\index.html" "%PACKAGE_DIR%\frontend\" >nul

REM 复制文档
copy /y "README.md" "%PACKAGE_DIR%\" >nul
copy /y "安装包说明.md" "%PACKAGE_DIR%\" >nul
copy /y "SETUP.md" "%PACKAGE_DIR%\docs\" >nul

REM 复制启动脚本
copy /y "一键启动.bat" "%PACKAGE_DIR%\" >nul

echo [4/5] 创建 .env 模板...
(
echo # 应用配置
echo APP_NAME=AI Tutor
echo APP_VERSION=1.0.0
echo DEBUG=True
echo.
echo # 服务器配置
echo HOST=0.0.0.0
echo PORT=8000
echo.
echo # 数据库配置 - MySQL
echo MYSQL_HOST=localhost
echo MYSQL_PORT=3306
echo MYSQL_USER=root
echo MYSQL_PASSWORD=root
echo MYSQL_DATABASE=ai_tutor
echo.
echo # 数据库配置 - Redis
echo REDIS_HOST=localhost
echo REDIS_PORT=6379
echo REDIS_PASSWORD=
echo REDIS_DB=0
echo.
echo # JWT配置
echo SECRET_KEY=请修改为你的随机密钥
echo ALGORITHM=HS256
echo ACCESS_TOKEN_EXPIRE_MINUTES=1440
echo.
echo # 硅基流动 API 配置
echo OPENAI_API_KEY=sk-请填写你的API密钥
echo OPENAI_API_BASE=https://api.siliconflow.cn/v1
echo.
echo # 模型配置
echo LLM_MODEL=deepseek-ai/DeepSeek-V3
echo TEMPERATURE=0.3
echo MAX_TOKENS=4096
echo VISION_MODEL=Qwen/Qwen2.5-VL-32B-Instruct
echo.
echo # 向量模型配置
echo EMBEDDING_MODEL=text-embedding-v3
echo DASHSCOPE_API_KEY=请填写你的DashScope密钥
echo DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/api/v1
) > "%PACKAGE_DIR%\backend\.env.example"

echo [5/5] 打包压缩...
cd "%PACKAGE_DIR%\.."

REM 使用 PowerShell 压缩
powershell -Command "Compress-Archive -Path '%PACKAGE_NAME%' -DestinationPath '%ZIP_NAME%' -Force"

echo.
echo ==========================================
echo  安装包制作完成！
echo  文件名: %ZIP_NAME%
echo  路径: %PROJECT_DIR%%ZIP_NAME%
echo ==========================================
echo.
pause
