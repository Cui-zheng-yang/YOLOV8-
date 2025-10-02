#!/bin/bash
# start.sh - Linux/Mac启动脚本

echo "=========================================="
echo "  YOLOv8 跌倒检测系统 - 启动脚本"
echo "=========================================="

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 进入后端目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查依赖..."
pip install -q -r requirements.txt

# 创建必要的目录
mkdir -p models/weights
mkdir -p logs

# 启动后端服务
echo "启动后端服务..."
python app.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端服务
echo "启动前端服务..."
cd ../frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!

echo "=========================================="
echo "  ✅ 系统启动成功！"
echo "=========================================="
echo "前端地址: http://localhost:8080"
echo "后端API: http://localhost:5000/api"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

# ==========================================
# start.bat - Windows启动脚本
# ==========================================

: <<'BATCH'
@echo off
chcp 65001 >nul
echo ==========================================
echo   YOLOv8 跌倒检测系统 - 启动脚本
echo ==========================================

REM 检查Python
echo 检查Python版本...
python --version

REM 进入后端目录
cd backend

REM 创建虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -q -r requirements.txt

REM 创建目录
if not exist "models\weights" mkdir models\weights
if not exist "logs" mkdir logs

REM 启动后端
echo 启动后端服务...
start /B python app.py

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
echo 启动前端服务...
cd ..\frontend
start /B python -m http.server 8080

echo ==========================================
echo   ✅ 系统启动成功！
echo ==========================================
echo 前端地址: http://localhost:8080
echo 后端API: http://localhost:5000/api
echo.
echo 按任意键停止服务...
echo ==========================================
pause >nul

REM 停止服务
taskkill /F /IM python.exe >nul 2>&1
echo 服务已停止
pause
BATCH