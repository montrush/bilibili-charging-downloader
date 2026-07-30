@echo off
chcp 65001 >nul
REM B站充电视频下载器 - Windows原生运行(无需Docker)
REM 前提: 已装Python3.8+, 已下载BBDown.exe放到本目录或PATH, 已装ffmpeg

cd /d %~dp0

echo === B站充电视频下载器 (Windows) ===

REM 检查BBDown
where BBDown.exe >nul 2>&1
if %errorlevel% neq 0 (
    if not exist BBDown.exe (
        echo [错误] 找不到BBDown.exe
        echo 请从 https://github.com/nilaoda/BBDown/releases 下载 BBDown.exe 放到本目录
        pause
        exit /b 1
    )
)

REM 检查Python依赖
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装依赖] pip install -r server\requirements.txt
    pip install -r server\requirements.txt
)

REM 构建前端(如果dist不存在)
if not exist web\dist (
    echo [构建前端] 需要Node.js, 正在构建...
    cd web
    if not exist node_modules (
        echo [安装前端依赖] npm install
        call npm install
    )
    echo [构建] npm run build
    call npm run build
    cd ..
)

echo.
echo 启动服务: http://localhost:8000
echo 浏览器打开上面的地址, 扫码登录B站账号后开始下载
echo.
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
pause
