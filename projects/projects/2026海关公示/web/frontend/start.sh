#!/bin/bash
# 启动前端开发服务器

cd "$(dirname "$0")"

echo "安装依赖..."
pnpm install

echo "启动开发服务器..."
pnpm dev
