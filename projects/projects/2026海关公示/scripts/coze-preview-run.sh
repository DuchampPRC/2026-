#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

export PORT=5000

# 清理 5000 端口残留进程
fuser -k 5000/tcp 2>/dev/null || true
sleep 1

echo "[run] 启动海关公示数据分析服务（端口 5000）..."
cd web
exec python api.py
