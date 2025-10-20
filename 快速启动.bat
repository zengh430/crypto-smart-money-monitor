@echo off
chcp 65001 > nul
echo.
echo ====================================
echo   加密货币监控系统
echo ====================================
echo.
echo 正在启动程序...
echo.

python hyperliquid_monitor.py

if %errorlevel% neq 0 (
    echo.
    echo 程序运行出错！
    pause
)
