"""
سامانه سرور زنده و مانیتورینگ خودکار فایل اکسل ادعاها
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.excel_live_parser import parse_excel_claims

WEB_DIR = os.path.join(BASE_DIR, "web")
EXCEL_PATH = os.path.join(BASE_DIR, "فایل_اکسل_مرجع", "claim metro L100.xlsx")
DATA_JSON_PATH = os.path.join(BASE_DIR, "data", "claims_metro_line10.json")

PORT = 8090

# Global state
LOCK = threading.Lock()
LATEST_DATA = {}
LATEST_VERSION = int(time.time() * 1000)
LAST_UPDATED_TIME = ""
WATCHER_RUNNING = True


def reload_excel(force=False):
    global LATEST_DATA, LATEST_VERSION, LAST_UPDATED_TIME
    if not os.path.exists(EXCEL_PATH):
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ فایل اکسل یافت نشد: {EXCEL_PATH}")
        return False

    parsed = None
    last_err = None
    for attempt in range(4):
        try:
            parsed = parse_excel_claims(EXCEL_PATH)
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

        # Update data/claims_metro_line10.json as well
        try:
            with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        emp_count = len(parsed.get('employer_claims', []))
        sub_count = len(parsed.get('subcontractor_claims', []))
        print(f"[{now_str}] ✓ اکسل با موفقیت بازخوانی شد: {emp_count} ادعای کارفرما + {sub_count} پرونده پیمانکاران | فایل: {os.path.basename(EXCEL_PATH)}")
        return True
    else:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ خطا در بازخوانی اکسل: {last_err}")
        return False


def excel_watcher_thread():
    last_mtime = 0
    if os.path.exists(EXCEL_PATH):
        try:
            last_mtime = os.path.getmtime(EXCEL_PATH)
        except Exception:
            last_mtime = 0

    reload_excel(force=True)

    while WATCHER_RUNNING:
        time.sleep(1.0)
        if not os.path.exists(EXCEL_PATH):
            continue
        try:
            cur_mtime = os.path.getmtime(EXCEL_PATH)
            if cur_mtime != last_mtime:
                time.sleep(0.4)  # Wait for Excel lock release
                last_mtime = os.path.getmtime(EXCEL_PATH)
                print(f"\n[🔄 شناسایی تغییر در اکسل] کاربر فایل اکسل را ذخیره کرد. در حال همگام‌سازی لحظه‌ای داشبورد...")
                reload_excel()
        except Exception:
            pass


class LiveDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
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
                    "file_path": EXCEL_PATH,
                    "exists": os.path.exists(EXCEL_PATH)
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

        elif path in ("/", "/index.html"):
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
    print(" 🚀 سامانه داشبورد زنده و پویای کلیم‌ها (همگام‌سازی خودکار با اکسل)")
    print(" پروژه خط ۱۰ متروی تهران — قرارگاه سازندگی خاتم‌الانبیاء (ص)")
    print("-" * 72)
    print(f" 📂 فایل اکسل تحت رصد:")
    print(f"    {EXCEL_PATH}")
    print(f" 🌐 آدرس داشبورد در مرورگر: http://localhost:{PORT}")
    print(" 💡 ویژگی زنده: هر تغییری در اکسل بدهید و Ctrl+S بزنید، داشبورد آنی آپدیت می‌شود.")
    print(" 🛑 برای توقف سرور کلیدهای Ctrl+C را در این پنجره بزنید.")
    print("=" * 72)

    def open_browser():
        time.sleep(1.0)
        webbrowser.open(f"http://localhost:{PORT}")

    t_browser = threading.Thread(target=open_browser, daemon=True)
    t_browser.start()

    t_watcher = threading.Thread(target=excel_watcher_thread, daemon=True)
    t_watcher.start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nدر حال خاموش کردن سرور زنده...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
