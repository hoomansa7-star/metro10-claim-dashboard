"""
سامانه سرور زنده و مانیتورینگ خودکار فایل اکسل
ویژه خط ۱۰ متروی تهران — قرارگاه سازندگی خاتم‌الانبیاء (ص)
"""
import sys
import os
import time
import json
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from excel_live_parser import parse_excel_claims

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

# Priority list of Excel paths to monitor
WATCH_PATHS = [
    os.path.join(BASE_DIR, "فایل_اکسل_مرجع", "claim metro L100.xlsx"),
    os.path.join(os.path.dirname(BASE_DIR), "میزان کلیم", "claim metro L100.xlsx"),
    os.path.join(r"C:\Users\Hooman\Desktop\پکیج_ارائه_کلیم_خط۱۰\فایل_اکسل_مرجع", "claim metro L100.xlsx"),
    os.path.join(BASE_DIR, "claim metro L100.xlsx")
]

PORT = 8090

# Global state
LOCK = threading.Lock()
LATEST_DATA = {}
LATEST_VERSION = int(time.time() * 1000)
LAST_UPDATED_TIME = ""
ACTIVE_EXCEL_PATH = ""
WATCHER_RUNNING = True

def get_most_recent_excel_path():
    candidates = []
    for p in WATCH_PATHS:
        if os.path.exists(p):
            try:
                candidates.append((os.path.getmtime(p), p))
            except Exception:
                pass
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return WATCH_PATHS[0]

def reload_excel(target_path=None, force=False):
    global LATEST_DATA, LATEST_VERSION, LAST_UPDATED_TIME, ACTIVE_EXCEL_PATH
    if not target_path:
        target_path = get_most_recent_excel_path()
    
    if not os.path.exists(target_path):
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ فایل اکسل یافت نشد: {target_path}")
        return False

    # Retry loop to handle Windows Excel file lock during save
    parsed = None
    last_err = None
    for attempt in range(4):
        try:
            parsed = parse_excel_claims(target_path)
            break
        except PermissionError:
            time.sleep(0.35)
        except Exception as e:
            last_err = e
            time.sleep(0.2)

    if parsed:
        now_str = time.strftime("%H:%M:%S")
        with LOCK:
            LATEST_DATA = parsed
            LATEST_VERSION = int(time.time() * 1000)
            LAST_UPDATED_TIME = now_str
            ACTIVE_EXCEL_PATH = target_path

        emp_count = len(parsed.get('employer_claims', []))
        sub_count = len(parsed.get('subcontractor_claims', []))
        print(f"[{now_str}] ✓ اکسل با موفقیت بازخوانی شد: {emp_count} ادعای کارفرما + {sub_count} پرونده پیمانکاران | فایل: {os.path.basename(os.path.dirname(target_path))}\\{os.path.basename(target_path)}")
        return True
    else:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ خطا در بازخوانی اکسل: {last_err}")
        return False

def excel_watcher_thread():
    last_mtimes = {}
    for p in WATCH_PATHS:
        if os.path.exists(p):
            try:
                last_mtimes[p] = os.path.getmtime(p)
            except Exception:
                last_mtimes[p] = 0

    # Initial load
    reload_excel(force=True)

    while WATCHER_RUNNING:
        time.sleep(1.0)
        for p in WATCH_PATHS:
            if not os.path.exists(p):
                continue
            try:
                cur_mtime = os.path.getmtime(p)
                prev_mtime = last_mtimes.get(p, 0)
                if cur_mtime != prev_mtime:
                    # File was modified / saved in Excel!
                    time.sleep(0.4) # Wait for Excel to release lock
                    last_mtimes[p] = os.path.getmtime(p)
                    print(f"\n[🔄 شناسایی تغییر در اکسل] کاربر فایل اکسل را ذخیره کرد ({os.path.basename(p)}). در حال همگام‌سازی لحظه‌ای داشبورد...")
                    reload_excel(target_path=p)
            except Exception:
                pass

class LiveDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        # Suppress routine polling logs to keep terminal quiet and readable
        if len(args) > 0 and "/api/version" in str(args[0]):
            return
        super().log_message(format, *args)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            with LOCK:
                data_bytes = json.dumps(LATEST_DATA, ensure_ascii=False).encode('utf-8')
            self.wfile.write(data_bytes)
            return

        elif path == "/api/version":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            with LOCK:
                res = {
                    "version": LATEST_VERSION,
                    "last_updated": LAST_UPDATED_TIME,
                    "file_path": ACTIVE_EXCEL_PATH,
                    "exists": os.path.exists(ACTIVE_EXCEL_PATH) if ACTIVE_EXCEL_PATH else False
                }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        elif path == "/api/sync":
            ok = reload_excel(force=True)
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": ok, 
                "version": LATEST_VERSION, 
                "time": LAST_UPDATED_TIME
            }).encode('utf-8'))
            return

        elif path == "/" or path == "/index.html":
            index_path = os.path.join(WEB_DIR, "index.html")
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        return super().do_GET()

def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, LiveDashboardHandler)
    print("=" * 72)
    print(" 🚀 سامانه داشبورد زنده و پویای امور قراردادها (همگام‌سازی خودکار با اکسل)")
    print(" پروژه خط ۱۰ متروی تهران — قرارگاه سازندگی خاتم‌الانبیاء (ص)")
    print("-" * 72)
    print(f" 📂 فایل اکسل تحت رصد:")
    print(f"    {get_most_recent_excel_path()}")
    print(f" 🌐 آدرس داشبورد در مرورگر: http://localhost:{PORT}")
    print(" 💡 ویژگی زنده: هر تغییری در اکسل بدهید و Ctrl+S بزنید، داشبورد آنی آپدیت می‌شود.")
    print(" 🛑 برای توقف سرور کلیدهای Ctrl+C را در این پنجره بزنید.")
    print("=" * 72)

    # Launch browser automatically
    def open_browser():
        time.sleep(1.0)
        webbrowser.open(f"http://localhost:{PORT}")

    t_browser = threading.Thread(target=open_browser, daemon=True)
    t_browser.start()

    # Start file watcher thread
    t_watcher = threading.Thread(target=excel_watcher_thread, daemon=True)
    t_watcher.start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nدر حال خاموش کردن سرور زنده...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
