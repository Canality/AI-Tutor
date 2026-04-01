@echo off
chcp 936 >nul
echo ==========================================
echo    AI Tutor - 高中数学数列智能辅导系统
echo    计算机设计大赛参赛作品
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    echo 请从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

echo [1/5] 检查虚拟环境...
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
)

echo [2/5] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

echo [3/5] 安装依赖...
pip install -q -r backend\requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    echo 请检查 backend\requirements.txt 文件是否存在
    pause
    exit /b 1
)

echo [4/5] 检查数据库配置...
if not exist "backend\.env" (
    echo [警告] 未找到 backend\.env 文件
    echo 请复制 backend\.env.example 为 backend\.env 并修改配置
    echo.
    echo 按任意键继续尝试启动...
    pause >nul
)

echo [5/5] 启动后端服务...
cd backend
start "AI Tutor 后端服务" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

echo.
echo ==========================================
echo  后端服务启动中...
echo  请等待 3-5 秒后访问: http://localhost:8000
echo  API文档: http://localhost:8000/docs
echo ==========================================
echo.
echo 提示:
echo 1. 如果无法访问，请检查 MySQL 和 Redis 是否已启动
echo 2. 首次启动需要配置 backend\.env 文件
echo 3. 保持此窗口运行，不要关闭
echo.
pause
