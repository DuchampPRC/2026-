#!/bin/bash
# 海关公示数据分析系统启动脚本

cd "$(dirname "$0")"

echo "安装后端依赖..."
cd backend || cd web
pip install -q fastapi uvicorn pandas python-multipart

echo "启动后端 API (端口 5000)..."
python api.py &
BACKEND_PID=$!

echo "安装前端依赖..."
cd ../frontend
pnpm install

echo "启动前端服务 (端口 5000)..."
pnpm dev &
FRONTEND_PID=$!

echo ""
echo "=== 启动完成 ==="
echo "后端 API: http://localhost:5000"
echo "前端页面: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
