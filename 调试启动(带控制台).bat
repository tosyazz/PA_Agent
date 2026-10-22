@echo off
chcp 936 >nul 2>&1
title PA Agent - 调试模式（会显示控制台）
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897
cd /d "%~dp0"
rem 排查启动崩溃时用这个：保留控制台窗口，异常会停住
python run.py
echo.
echo [调试] 程序已退出，错误码 %errorlevel%
pause
