@echo off
chcp 65001 >nul
echo =================== 重启后端服务 ===================
echo.
echo [1/3] 查找占用 8000/8001 端口的旧进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 LISTEN :8001 LISTEN"') do (
    echo     终止旧后端进程 PID=%%a ...
    taskkill //PID %%a //F >nul 2>&1
)

echo [2/3] 等待端口释放...
timeout /t 3 >nul

echo [3/3] 启动后端（端口 8001，--reload）...
cd /d "%~dp0backend"
start "AI-Agent后端(8001)" cmd //k "python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo.
echo =================== 完成 ===================
echo 后端: http://localhost:8001  文档: http://localhost:8001/docs
echo 前端: http://localhost:3000  (需单独 npm run dev)
pause
