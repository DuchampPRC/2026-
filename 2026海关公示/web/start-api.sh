#!/bin/bash
# 启动后端 API

cd "$(dirname "$0")"

echo "安装依赖..."
pip install -q fastapi uvicorn pandas python-multipart

echo "启动后端 API..."
python api.py
