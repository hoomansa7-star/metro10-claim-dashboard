"""
اسکریپت اجرای سامانه امور قراردادها (برنامه ۱)
"""
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
P1_DIR = os.path.join(BASE_DIR, "۱_سامانه_امور_قراردادها_و_۵۰۹۰")

if __name__ == "__main__":
    script = os.path.join(P1_DIR, "run_dashboard.py")
    subprocess.call([sys.executable, script], cwd=P1_DIR)
