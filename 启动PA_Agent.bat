@echo off
cd /d "%~dp0"

rem If a local proxy (Clash/Mihomo, port 7897) is listening, route this app
rem through it so the Binance / OKX public market endpoints can connect.
netstat -ano | findstr /c:":7897 " | findstr /c:"LISTENING" >nul
if not errorlevel 1 (
    set "HTTP_PROXY=http://127.0.0.1:7897"
    set "HTTPS_PROXY=http://127.0.0.1:7897"
)

python run.py
if errorlevel 1 (
    echo.
    echo [ERROR] PA Agent exited unexpectedly. See the messages above.
    pause
)
