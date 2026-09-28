"""
اسکریپت همگام‌سازی داده‌های اکسل و بروزرسانی خودکار داشبورد آنلاین در گیت‌هاب
پروژه خط ۱۰ متروی تهران — قرارگاه سازندگی خاتم‌الانبیاء (ص)
"""
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
P2_DIR = os.path.join(BASE_DIR, "۲_داشبورد_کلیم_ها_و_اکسل_زنده")
if P2_DIR not in sys.path:
    sys.path.insert(0, P2_DIR)

import sync_and_push as p2_sync

if __name__ == "__main__":
    p2_sync.sync_excel_to_web()
    p2_sync.push_to_github()
