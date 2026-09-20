"""
اسکریپت اجرای خودکار سامانه امور قراردادها و باز کردن داشبورد در مرورگر
"""
import sys
import os
import webbrowser
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import run_server

PORT = 8050

def open_browser():
    time.sleep(1.2)
    url = f"http://localhost:{PORT}"
    print(f"Opening dashboard in browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    t = threading.Thread(target=open_browser)
    t.daemon = True
    t.start()
    print(f"============================================================")
    print(f" سامانه امور قراردادها و مهندسی ادعا — خط ۱۰ متروی تهران")
    print(f" قرارگاه سازندگی خاتم‌الانبیاء (ص) — موسسه حرا")
    print(f" آدرس داشبورد: http://localhost:{PORT}")
    print(f" برای خروج کلیدهای Ctrl+C را فشار دهید.")
    print(f"============================================================")
    run_server(PORT)
