@echo off
chcp 65001 > nul

:loop
"C:\Users\sovet\miniconda3\python.exe" bot.py

echo Бот остановился, перезапуск через 3 секунды...
timeout /t 3 > nul
goto loop