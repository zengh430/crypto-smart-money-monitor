@echo off
chcp 65001 >nul
echo ========================================
echo   加密货币聪明钱监控系统
echo   推送更新到 GitHub
echo   作者: Howard Zeng
echo ========================================
echo.

:: 检查Git仓库
if not exist .git (
    echo [错误] 未找到Git仓库！请先运行 "上传到GitHub.bat"
    pause
    exit /b 1
)

:: 显示当前状态
echo [信息] 当前更改:
echo.
git status -s
echo.

:: 询问提交信息
set /p commit_msg="请输入提交信息 (按回车使用默认): "

if "%commit_msg%"=="" (
    set commit_msg=Update: 更新代码
)

:: 添加所有更改
echo.
echo [步骤1/3] 添加更改的文件...
git add .
if errorlevel 1 (
    echo [错误] 添加文件失败
    pause
    exit /b 1
)
echo [完成] 文件添加成功
echo.

:: 提交更改
echo [步骤2/3] 提交更改...
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo [信息] 没有新的更改需要提交
    echo.
    set /p continue="是否继续推送？(Y/N): "
    if /i not "%continue%"=="Y" (
        echo 操作已取消
        pause
        exit /b 0
    )
)
echo.

:: 推送到GitHub
echo [步骤3/3] 推送到GitHub...
git push origin main

if errorlevel 1 (
    echo.
    echo [错误] 推送失败！
    echo 尝试先拉取远程更改...
    git pull origin main --rebase
    echo.
    echo 重新推送...
    git push origin main
) else (
    echo.
    echo ========================================
    echo   ✓ 更新成功！
    echo ========================================
    echo.
    echo 项目地址:
    echo https://github.com/zengh430/crypto-smart-money-monitor
    echo.
)

echo.
echo 按任意键退出...
pause >nul
