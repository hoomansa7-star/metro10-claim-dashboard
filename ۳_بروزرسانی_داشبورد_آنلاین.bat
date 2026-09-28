@echo off
chcp 65001 > nul
title بروزرسانی خودکار داشبورد کلیم‌ها در گیت‌هاب
cd /d "%~dp0۲_داشبورد_کلیم_ها_و_اکسل_زنده"
python sync_and_push.py
pause
