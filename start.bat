@echo off
REM 启动 M3 游戏资产生成工作流 UI
REM 默认绑定 127.0.0.1（仅本机），安全启动
REM 如需局域网访问，把下面的 127.0.0.1 改成 0.0.0.0（注意安全风险）

chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

echo.
echo ====================================================
echo   M3 游戏资产生成工作流
echo   启动后浏览器会自动打开 http://127.0.0.1:8501
echo   Ctrl+C 可停止服务
echo ====================================================
echo.

python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false

pause
