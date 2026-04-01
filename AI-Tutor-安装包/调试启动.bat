@echo off
echo ==========================================
echo    AI Tutor - 调试启动模式
echo ==========================================
echo.

REM 显示当前目录
echo 当前目录: %CD%
echo.

REM 检查 Python
echo [检查] Python...
python --version
if errorlevel 1 (
    echo [错误] 未检测到 Python!
    echo 请安装 Python 3.9+ 并添加到系统 PATH
    pause
    exit /b 1
)
echo [OK] Python 已安装
echo.

REM 检查虚拟环境
echo [检查] 虚拟环境...
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 虚拟环境创建失败!
    pause
    exit /b 1
)
echo [OK] 虚拟环境已就绪
echo.

REM 激活虚拟环境
echo [激活] 虚拟环境...
call venv\Scripts\activate.bat
echo [OK] 虚拟环境已激活
echo.

REM 检查依赖
echo [检查] 依赖文件...
if not exist "backend\requirements.txt" (
    echo [错误] 未找到 backend\requirements.txt
    pause
    exit /b 1
)
echo [OK] 依赖文件存在
echo.

REM 安装依赖
echo [安装] 依赖...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败!
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

REM 检查环境变量
echo [检查] 环境变量...
if not exist "backend\.env" (
    echo [警告] 未找到 backend\.env 文件
    echo 请复制 backend\.env.example 为 backend\.env 并配置
    echo.
    echo 是否继续? (Y/N)
    choice /c YN /n
    if errorlevel 2 exit /b 1
)
echo [OK] 环境变量检查完成
echo.

REM 启动服务
echo [启动] 后端服务...
echo 正在启动，请稍候...
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
cd ..

echo.
echo [服务已停止]
pause
