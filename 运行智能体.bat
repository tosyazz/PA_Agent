@echo off
chcp 936 >nul 2>&1
title PA Agent - AI K线分析助手
rem 代理由程序自动探测：本地 7897/7890 可连通则走代理，否则直连
rem 如需强制指定代理，取消下面两行注释并改成你的端口
rem set HTTP_PROXY=http://127.0.0.1:7897
rem set HTTPS_PROXY=http://127.0.0.1:7897
cd /d "%~dp0"
rem 用 pythonw 启动：不弹控制台窗口，程序日志显示在「控制台」标签页
start "" pythonw.exe run.py
exit /b 0
