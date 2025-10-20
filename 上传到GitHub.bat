@echo off
chcp 65001 >nul
echo ========================================
echo   加密货币聪明钱监控系统
echo   一键上传到 GitHub
echo   作者: Howard Zeng
echo ========================================
echo.

:: 检查是否已经初始化git
if exist .git (
    echo [信息] Git仓库已存在
) else (
    echo [步骤1/4] 初始化Git仓库...
    git init
    if errorlevel 1 (
        echo [错误] Git初始化失败！请确保已安装Git
        pause
        exit /b 1
    )
    echo [完成] Git仓库初始化成功
    echo.
)

:: 添加远程仓库
echo [步骤2/4] 配置远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/zengh430/crypto-smart-money-monitor.git
if errorlevel 1 (
    echo [错误] 添加远程仓库失败
    pause
    exit /b 1
)
echo [完成] 远程仓库配置成功
echo.

:: 添加所有文件
echo [步骤3/4] 添加文件到Git...
git add .
if errorlevel 1 (
    echo [错误] 添加文件失败
    pause
    exit /b 1
)
echo [完成] 文件添加成功
echo.

:: 提交
echo [步骤4/4] 提交更改...
git commit -m "Initial commit: Crypto Smart Money Monitor

- AI-assisted development using Claude Code
- Bilingual support (Chinese/English) with 95%% coverage
- Multi-source data integration (Hyperliquid + OKX)
- Real-time market monitoring and visualization
- Whale position tracking with detailed analytics

Built by Howard Zeng"

if errorlevel 1 (
    echo [警告] 提交可能失败或没有新更改
)
echo.

:: 推送到GitHub
echo [推送] 正在上传到GitHub...
echo.
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo [错误] 推送失败！可能的原因：
    echo   1. 需要先登录GitHub（如果是首次推送）
    echo   2. 仓库已存在内容（需要先pull）
    echo   3. 网络连接问题
    echo.
    echo 尝试强制推送吗？（可能覆盖远程内容）
    set /p confirm="输入 YES 确认强制推送，或按回车取消: "
    if /i "%confirm%"=="YES" (
        echo.
        echo [警告] 执行强制推送...
        git push -u origin main --force
    )
) else (
    echo.
    echo ========================================
    echo   ✓ 上传成功！
    echo ========================================
    echo.
    echo 项目地址:
    echo https://github.com/zengh430/crypto-smart-money-monitor
    echo.
)

echo.
echo 按任意键退出...
pause >nul
