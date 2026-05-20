#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 设置 PYTHONPATH 以支持 customs_pipeline 模块导入
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
export PORT=5000

echo "[deploy-run] 启动海关公示数据分析服务（端口 5000）..."
cd web
exec python api.py
