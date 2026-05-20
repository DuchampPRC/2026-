#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "[build] 安装前端依赖..."
cd web/frontend
pnpm install --no-frozen-lockfile 2>/dev/null || true

echo "[build] 构建前端..."
pnpm build

echo "[build] 安装后端依赖..."
cd ../..
pip install -q fastapi uvicorn pandas python-multipart

echo "[build] 完成"
