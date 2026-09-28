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

P2_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(P2_DIR)
if P2_DIR not in sys.path:
    sys.path.insert(0, P2_DIR)

from core.excel_live_parser import parse_excel_claims

EXCEL_PATH = os.path.join(P2_DIR, "فایل_اکسل_مرجع", "claim metro L100.xlsx")


def sync_excel_to_web():
    if not os.path.exists(EXCEL_PATH):
        print(f"⚠ فایل اکسل در مسیر زیر یافت نشد:\n  {EXCEL_PATH}")
        return False

    print(f"🔄 در حال استخراج آخرین اطلاعات از اکسل مرجع: {os.path.basename(EXCEL_PATH)}")
    try:
        data = parse_excel_claims(EXCEL_PATH)
    except Exception as e:
        print(f"⚠ خطا در خواندن اکسل: {e}")
        return False

    emp_count = len(data.get('employer_claims', []))
    sub_count = len(data.get('subcontractor_claims', []))
    print(f"✓ داده‌ها با موفقیت پردازش شد: {emp_count} کلیم کارفرما + {sub_count} پرونده پیمانکاران.")

    # 1. Update JSON files
    json_targets = [
        os.path.join(P2_DIR, "data", "claims_metro_line10.json"),
        os.path.join(ROOT_DIR, "data", "claims_metro_line10.json"),
        os.path.join(ROOT_DIR, "۱_سامانه_امور_قراردادها_و_۵۰۹۰", "data", "claims_metro_line10.json"),
    ]
    for p in json_targets:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✔ فایل {os.path.relpath(p, ROOT_DIR)} بروز شد.")
        except Exception as e:
            pass

    # 2. Update HTML presentations
    html_targets = [
        os.path.join(P2_DIR, "web", "claims_presentation.html"),
        os.path.join(P2_DIR, "web", "index.html"),
        os.path.join(ROOT_DIR, "web", "claims_presentation.html"),
    ]
    json_str = json.dumps(data, ensure_ascii=False)
    for p in html_targets:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                html_content = f.read()

            for marker in ("let ALL_DATA = ", "const ALL_DATA = "):
                idx = html_content.find(marker)
                if idx != -1:
                    end_idx = html_content.find(";\n", idx)
                    if end_idx == -1:
                        end_idx = html_content.find(";", idx)
                    if end_idx != -1:
                        new_html = html_content[:idx + len(marker)] + json_str + html_content[end_idx:]
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(new_html)
                        print(f"✔ داده‌های درونی {os.path.relpath(p, ROOT_DIR)} بروز شد.")
                    break
    return True


def push_to_github():
    print("\n📦 در حال بررسی تغییرات و ارسال به گیت‌هاب...")
    try:
        st = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT_DIR, text=True, encoding="utf-8")
        if not st.strip():
            print("✨ هیچ تغییری برای ارسال به گیت‌هاب وجود ندارد. سایت آنلاین با آخرین داده‌ها همگام است!")
            return

        subprocess.check_call(["git", "add", "."], cwd=ROOT_DIR)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"update: sync claims dashboard data ({now_str})"
        subprocess.check_call(["git", "commit", "-m", commit_msg], cwd=ROOT_DIR)
        print("🚀 در حال پوش (Push) به گیت‌هاب...")
        subprocess.check_call(["git", "push", "origin", "main"], cwd=ROOT_DIR)
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
