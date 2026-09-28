"""
سرور محلی و API داشبورد امور قراردادها و تولید اسناد
ویژه پروژه خط ۱۰ مترو تهران - قرارگاه سازندگی خاتم‌الانبیاء
استفاده از کتابخانه استاندارد پایتون بدون نیاز به نصب فریم‌ورک‌های جانبی
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import os
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

from core.models import ContractInfo, PaymentCertificate, WorkFrontEvent, Guarantee
from core.circular_5090 import Circular5090Engine
from core.legal_engine import LegalEngine
from core.docx_generator import DocxGenerator
from core.excel_generator import ExcelGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "metro_line10_data.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_documents")
WEB_DIR = os.path.join(BASE_DIR, "web")

os.makedirs(OUTPUT_DIR, exist_ok=True)


class ProjectDataManager:
    """مدیریت ذخیره‌سازی و خواندن داده‌های پیمان خط ۱۰"""

    @classmethod
    def load_data(cls) -> Dict[str, Any]:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"contract": {}, "certificates": [], "events": [], "guarantees": []}

    @classmethod
    def save_data(cls, data: Dict[str, Any]):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_full_analysis(cls) -> Dict[str, Any]:
        data = cls.load_data()
        contract = ContractInfo(**data.get("contract", {}))
        certs = [PaymentCertificate(**c) for c in data.get("certificates", [])]
        events = [WorkFrontEvent(**e) for e in data.get("events", [])]
        guars = [Guarantee(**g) for g in data.get("guarantees", [])]

        analysis = Circular5090Engine.perform_overlap_analysis(certs, events, contract)

        # محاسبه شاخص‌های کلی مالی
        total_claimed = sum(c.claimed_amount for c in certs if c.cert_type != "advance")
        total_approved = sum(c.approved_amount for c in certs if c.cert_type != "advance")
        total_paid = sum(c.paid_amount for c in certs)
        total_unpaid_approved = sum((c.approved_amount - c.paid_amount) for c in certs if c.approved_amount > c.paid_amount)

        ceiling_usage_percent = (total_approved / contract.initial_amount * 100) if contract.initial_amount > 0 else 0

        # تبدیل شیءها به دیکشنری جهت بازگردانی JSON
        return {
            "contract": contract.model_dump(),
            "certificates": [c.model_dump() for c in analysis["processed_certificates"]],
            "events": [e.model_dump() for e in events],
            "guarantees": [g.model_dump() for g in guars],
            "analysis": {
                "raw_financial_t_sum": analysis["raw_financial_t_sum"],
                "raw_technical_days_sum": analysis["raw_technical_days_sum"],
                "financial_calendar_days": analysis["financial_calendar_days"],
                "technical_calendar_days": analysis["technical_calendar_days"],
                "overlap_days_count": analysis["overlap_days_count"],
                "net_justified_delay_days": analysis["net_justified_delay_days"],
                "initial_finish_date": analysis["initial_finish_date"],
                "new_finish_date": analysis["new_finish_date"],
                "extension_months": analysis["extension_months"]
            },
            "financial_summary": {
                "total_claimed": total_claimed,
                "total_approved": total_approved,
                "total_paid": total_paid,
                "total_unpaid_approved": total_unpaid_approved,
                "ceiling_usage_percent": round(ceiling_usage_percent, 2),
                "remaining_ceiling_amount": (contract.initial_amount * 1.25) - total_approved
            }
        }


legal_engine = LegalEngine()
docx_gen = DocxGenerator(OUTPUT_DIR)
excel_gen = ExcelGenerator(OUTPUT_DIR)


class ContractDashboardHandler(SimpleHTTPRequestHandler):
    """مدیریت درخواست‌های وب و API داشبورد"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json_response(self, data: Any, status_code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if path in ("/claims", "/claims/", "/presentation"):
            self.send_response(302)
            self.send_header("Location", "/claims_presentation.html")
            self.end_headers()
            return

        if path == "/api/project":
            data = ProjectDataManager.get_full_analysis()
            self._send_json_response(data)
            return

        elif path == "/api/knowledge_base":
            query = urllib.parse.parse_qs(parsed.query).get("q", [""])[0]
            if query:
                results = legal_engine.search_knowledge(query)
            else:
                results = legal_engine.knowledge
            self._send_json_response(results)
            return

        elif path == "/api/contract_guide":
            guide_file = os.path.join(BASE_DIR, "data", "contract_guide_line10.json")
            items = []
            if os.path.exists(guide_file):
                with open(guide_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
            query = urllib.parse.parse_qs(parsed.query).get("q", [""])[0].strip().lower()
            if query:
                items = [it for it in items if query in it.get("subject", "").lower() or query in it.get("clause_ref", "").lower()]
            self._send_json_response(items)
            return

        elif path == "/api/claims":
            claims_file = os.path.join(BASE_DIR, "data", "claims_metro_line10.json")
            if os.path.exists(claims_file):
                with open(claims_file, "r", encoding="utf-8") as f:
                    claims_data = json.load(f)
                self._send_json_response(claims_data)
            else:
                self._send_json_response({"error": "claims file not found"}, 404)
            return

        elif path == "/api/documents":
            docs = []
            if os.path.exists(OUTPUT_DIR):
                for f in os.listdir(OUTPUT_DIR):
                    fpath = os.path.join(OUTPUT_DIR, f)
                    if os.path.isfile(fpath):
                        stat = os.stat(fpath)
                        docs.append({
                            "filename": f,
                            "size_kb": round(stat.st_size / 1024, 1),
                            "modified": stat.st_mtime,
                            "download_url": f"/download/{urllib.parse.quote(f)}"
                        })
            self._send_json_response(docs)
            return

        elif path.startswith("/download/"):
            fname = urllib.parse.unquote(path[len("/download/"):])
            fpath = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(fpath) and os.path.isfile(fpath):
                self.send_response(200)
                content_type = "application/octet-stream"
                if fname.endswith(".docx"):
                    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif fname.endswith(".xlsx"):
                    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{urllib.parse.quote(fname)}")
                self.send_header("Content-Length", str(os.path.getsize(fpath)))
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "File not found")
                return

        # در غیر این صورت سرو فایل‌های استاتیک فرانت‌اند (HTML/JS/CSS)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        payload = json.loads(body) if body else {}

        if path == "/api/contract":
            data = ProjectDataManager.load_data()
            data["contract"].update(payload)
            ProjectDataManager.save_data(data)
            self._send_json_response({"status": "success", "message": "اطلاعات پیمان با موفقیت ذخیره شد."})
            return

        elif path == "/api/certificates":
            data = ProjectDataManager.load_data()
            certs = data.get("certificates", [])
            # بررسی ویرایش یا افزودن
            cert_id = payload.get("id") or f"cert-{len(certs) + 1}"
            payload["id"] = cert_id
            existing_idx = next((i for i, c in enumerate(certs) if c.get("id") == cert_id), None)
            if existing_idx is not None:
                certs[existing_idx] = payload
            else:
                certs.append(payload)
            data["certificates"] = certs
            ProjectDataManager.save_data(data)
            self._send_json_response({"status": "success", "message": "صورت‌وضعیت با موفقیت ثبت گردید."})
            return

        elif path == "/api/events":
            data = ProjectDataManager.load_data()
            events = data.get("events", [])
            ev_id = payload.get("id") or f"event-{len(events) + 1}"
            payload["id"] = ev_id
            existing_idx = next((i for i, e in enumerate(events) if e.get("id") == ev_id), None)
            if existing_idx is not None:
                events[existing_idx] = payload
            else:
                events.append(payload)
            data["events"] = events
            ProjectDataManager.save_data(data)
            self._send_json_response({"status": "success", "message": "رویداد و معارض با موفقیت ثبت گردید."})
            return

        elif path == "/api/generate_doc":
            doc_type = payload.get("doc_type")
            data = ProjectDataManager.load_data()
            contract = ContractInfo(**data.get("contract", {}))
            certs = [PaymentCertificate(**c) for c in data.get("certificates", [])]
            events = [WorkFrontEvent(**e) for e in data.get("events", [])]
            guars = [Guarantee(**g) for g in data.get("guarantees", [])]
            analysis = Circular5090Engine.perform_overlap_analysis(certs, events, contract)

            generated_file = ""
            if doc_type == "delay_claim":
                generated_file = docx_gen.generate_delay_claim_document(contract, analysis)
            elif doc_type == "payment_letter":
                last_cert = certs[-1] if certs else PaymentCertificate(id="1", cert_number="۵", submission_date="1402/10/06", claimed_amount=2950000000000, approved_amount=2950000000000)
                context = {
                    "cert_number": last_cert.cert_number,
                    "submission_date": last_cert.submission_date,
                    "amount": last_cert.paid_amount or last_cert.approved_amount,
                    "delay_days": last_cert.total_delay_days,
                    "t_days": last_cert.justified_delay_days
                }
                generated_file = docx_gen.generate_claim_letter(contract, "payment_delay", context)
            elif doc_type == "obstacle_letter":
                ev = events[0] if events else WorkFrontEvent(id="1", station_or_shaft="شفت ورودی TBM دریاچه", event_type="معارض تاسیساتی لوله گاز", start_date="1401/06/10", description="برخورد با خط لوله ۳۰ اینچ گاز")
                context = {
                    "site_name": ev.station_or_shaft,
                    "obstacle_desc": f"{ev.event_type} - {ev.description}",
                    "start_date": ev.start_date
                }
                generated_file = docx_gen.generate_claim_letter(contract, "utility_obstacle", context)
            elif doc_type == "ceiling_letter":
                context = {"used_percent": 24.5}
                generated_file = docx_gen.generate_claim_letter(contract, "ceiling_25_percent", context)
            elif doc_type == "site_minutes":
                ev = events[0] if events else WorkFrontEvent(id="1", station_or_shaft="کارگاه شفت ورودی TBM دریاچه چیتگر", event_type="معارض تاسیساتی لوله گاز", start_date="1402/04/10", description="برخورد با خط لوله ۳۰ اینچ گاز")
                generated_file = docx_gen.generate_site_minutes(contract, ev)
            elif doc_type == "excel_full":
                generated_file = excel_gen.generate_full_contract_workbook(contract, analysis, guars)
            else:
                self._send_json_response({"status": "error", "message": "نوع سند درخواستی نامعتبر است."}, status_code=400)
                return

            fname = os.path.basename(generated_file)
            self._send_json_response({
                "status": "success",
                "filename": fname,
                "download_url": f"/download/{urllib.parse.quote(fname)}",
                "message": f"سند {fname} با موفقیت تولید شد."
            })
            return

        self.send_error(404, "Endpoint not found")


def run_server(port: int = 8050):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, ContractDashboardHandler)
    print(f"Server started and listening on http://0.0.0.0:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass
    run_server(port)
