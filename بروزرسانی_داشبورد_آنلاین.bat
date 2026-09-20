@echo off
chcp 65001 > nul
python "%~dp0sync_and_push.py"
pause
