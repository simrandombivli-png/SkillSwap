
@echo off
title SkillSwap Launcher

cd /d "%~dp0"

echo Starting SkillSwap backend...
start "SkillSwap Backend" cmd /k "python -m uvicorn main:app --reload"

echo Waiting for backend to start...
timeout /t 4 /nobreak >nul

echo Opening SkillSwap frontend...
python skillswap_fe.py

echo.
echo SkillSwap frontend has closed.
pause
