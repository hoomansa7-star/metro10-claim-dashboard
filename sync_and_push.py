"""
اسکریپت همگام‌سازی داده‌های اکسل و بروزرسانی خودکار داشبورد آنلاین در گیت‌هاب
پروژه خط ۱۰ متروی تهران — قرارگاه سازندگی خاتم‌الانبیاء (ص)
"""
import os
import sys
import json
import time
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARSER_PATH = os.path.join(BASE_DIR, "سامانه_داشبورد_زنده_با_اکسل")
if PARSER_PATH not in sys.path:
    sys.path.append(PARSER_PATH)

try:
    from excel_live_parser import parse_excel_claims
except Exception as e:
    parse_excel_claims = None

EXCEL_CANDIDATES = [
    os.path.join(BASE_DIR, "میزان کلیم", "claim metro L100.xlsx"),
    os.path.join(BASE_DIR, "سامانه_داشبورد_زنده_با_اکسل", "فایل_اکسل_مرجع", "claim metro L100.xlsx"),
    os.path.join(BASE_DIR, "پکیج_ارائه_کلیم_خط۱۰", "فایل_اکسل_مرجع", "claim metro L100.xlsx"),
    os.path.join(BASE_DIR, "claim metro L100.xlsx"),
]


def find_latest_excel():
    existing = [(os.path.getmtime(p), p) for p in EXCEL_CANDIDATES if os.path.exists(p)]
    if existing:
        existing.sort(reverse=True)
        return existing[0][1]
    return None


def sync_excel_to_web():
    excel_path = find_latest_excel()
    if not excel_path or not parse_excel_claims:
        print("ℹ از فایل‌های JSON موجود استفاده می‌شود.")
        return False

    print(f"🔄 در حال استخراج آخرین اطلاعات از اکسل: {os.path.basename(excel_path)}")
    try:
        data = parse_excel_claims(excel_path)
    except Exception as e:
        print(f"⚠ خطا در خواندن اکسل: {e}")
        return False

    # 1. Update data/claims_metro_line10.json
    claims_json_path = os.path.join(BASE_DIR, "data", "claims_metro_line10.json")
    with open(claims_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✔ فایل {os.path.basename(claims_json_path)} با موفقیت بروز شد.")

    # 2. Update web/claims_presentation.html ALL_DATA
    html_path = os.path.join(BASE_DIR, "web", "claims_presentation.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        marker = "const ALL_DATA = "
        idx = html_content.find(marker)
        if idx != -1:
            end_idx = html_content.find(";\n", idx)
            if end_idx == -1:
                end_idx = html_content.find(";", idx)
            if end_idx != -1:
                json_str = json.dumps(data, ensure_ascii=False)
                new_html = html_content[:idx + len(marker)] + json_str + html_content[end_idx:]
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(new_html)
                print(f"✔ داده‌های درون‌برنامه‌ای داشبورد وب ({os.path.basename(html_path)}) بروز شد.")
    return True


def push_to_github():
    print("\n📦 در حال بررسی تغییرات و ارسال به گیت‌هاب...")
    try:
        # Check status
        st = subprocess.check_output(["git", "status", "--porcelain"], cwd=BASE_DIR, text=True, encoding="utf-8")
        if not st.strip():
            print("✨ هیچ تغییری برای ارسال به گیت‌هاب وجود ندارد. سایت آنلاین با آخرین داده‌ها همگام است!")
            return

        subprocess.check_call(["git", "add", "."], cwd=BASE_DIR)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"update: sync claims dashboard data ({now_str})"
        subprocess.check_call(["git", "commit", "-m", commit_msg], cwd=BASE_DIR)
        print("🚀 در حال پوش (Push) به گیت‌هاب...")
        subprocess.check_call(["git", "push", "origin", "main"], cwd=BASE_DIR)
        print("\n🎉 بروزرسانی با موفقیت انجام شد!")
        print("🌐 ظرف ۳۰ الی ۶۰ ثانیه آینده تغییرات در آدرس زیر آنلاین خواهد شد:")
        print("👉 https://hoomansa7-star.github.io/metro10-claim-dashboard/web/claims_presentation.html")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ خطا در فرآیند گیت: {e}")


if __name__ == "__main__":
    print("=" * 68)
    print("  سامانه بروزرسانی خودکار داشبورد کلیم‌های خط ۱۰ مترو در گیت‌هاب")
    print("=" * 68)
    sync_excel_to_web()
    push_to_github()
    print("=" * 68)
