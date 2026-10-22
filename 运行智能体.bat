@echo off
chcp 936 >nul 2>&1
title PA Agent - AI K线分析助手
rem TradingView 需要代理（Clash 默认端口 7897）；端口不同请改下面两行
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897
cd /d "%~dp0"
rem 用 pythonw 启动：不弹控制台窗口，程序日志显示在「控制台」标签页
start "" pythonw.exe run.py
exit /b 0
