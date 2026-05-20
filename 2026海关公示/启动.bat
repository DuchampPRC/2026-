@echo off
chcp 65001 >nul
title 2026海关公示 - 启动中

echo ========================================
echo    2026海关公示 启动脚本
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
set "WEB_DIR=%PROJECT_DIR%web"
set "FRONTEND_DIR=%WEB_DIR%\frontend"

:: 安装后端依赖（如果需要）
echo [1/3] 检查后端依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo     安装后端依赖...
    pip install fastapi uvicorn pandas python-docx openpyxl
)

:: 安装前端依赖（如果需要）
echo [2/3] 检查前端依赖...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo     安装前端依赖...
    cd /d "%FRONTEND_DIR%"
    call npm install -g pnpm
    call pnpm install
)

:: 启动后端服务
echo [3/3] 启动服务...
echo.
echo ----------------------------------------
echo  后端 API: http://localhost:5000
echo  前端页面: http://localhost:5173
echo ----------------------------------------
echo.
echo 按 Ctrl+C 停止服务
echo.

:: 启动后端（在新窗口）
start "2026海关公示 - 后端" cmd /k "cd /d "%WEB_DIR%" && python api.py"

:: 等待后端启动
timeout /t 3 >nul

:: 启动前端
cd /d "%FRONTEND_DIR%"
start "2026海关公示 - 前端" cmd /k "pnpm dev"

:: 打开浏览器
timeout /t 2 >nul
start http://localhost:5173

echo 启动完成！
pause
