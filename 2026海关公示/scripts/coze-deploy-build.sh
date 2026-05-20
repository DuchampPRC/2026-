#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "[deploy-build] 安装前端依赖..."
cd web/frontend
pnpm install --prefer-frozen-lockfile

echo "[deploy-build] 构建前端..."
pnpm build

echo "[deploy-build] 安装后端依赖..."
cd ../..
pip install -q fastapi uvicorn pandas python-multipart

echo "[deploy-build] 完成"
