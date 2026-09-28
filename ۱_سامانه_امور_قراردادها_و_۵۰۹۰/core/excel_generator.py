"""
موتور تولید دفترچه‌ها و گزارشات مالی اکسل (.xlsx) با فرمول‌های زنده و ساختار کاملاً راست‌به‌چپ (RTL)
مطابق ضوابط نظام فنی و اجرایی کشور و استانداردهای قرارگاه سازندگی خاتم‌الانبیاء
"""
import os
from typing import Dict, Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from core.models import ContractInfo, PaymentCertificate, WorkFrontEvent, Guarantee


class ExcelGenerator:
    """تولیدکننده شیت‌های استاندارد اکسل امور قراردادها"""

    def __init__(self, output_dir: Optional[str] = None):
        if not output_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "output_documents")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _apply_sheet_defaults(self, ws):
        """اعمال تنظیمات ضروری راست‌به‌چپ (RTL) و نمایش خطوط شبکه طبق قوانین سامانه"""
        ws.sheet_view.rightToLeft = True
        try:
            ws.views.sheetView[0].showGridLines = True
        except Exception:
            pass

    def _style_header_row(self, ws, row_idx: int, max_col: int, fill_color: str = "1E3A8A"):
        """اعمال رنگ و فونت سرستون‌ها"""
        header_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
        header_font = Font(name="Tahoma", size=10, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )
        for col in range(1, max_col + 1):
            cell = ws.cell(row=row_idx, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws.row_dimensions[row_idx].height = 28

    def _auto_fit_columns(self, ws, max_col: int):
        """تنظیم خودکار عرض ستون‌ها متناسب با محتوای فارسی"""
        for col in range(1, max_col + 1):
            col_letter = get_column_letter(col)
            max_len = 0
            for row in range(1, ws.max_row + 1):
                val = str(ws.cell(row=row, column=col).value or '')
                # طول تقریبی متن
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    def generate_full_contract_workbook(
        self,
        contract: ContractInfo,
        analysis_results: Dict[str, Any],
        guarantees: List[Guarantee],
        filename: str = "دفترچه_جامع_محاسبات_قرارداد_خط۱۰_مترو.xlsx"
    ) -> str:
        """
        تولید دفترچه محاسباتی جامع چند شیت شامل محاسبات ۵۰۹۰ با فرمول‌های زنده اکسل
        """
        wb = openpyxl.Workbook()

        # فونت‌ها و خطوط حاشیه عمومی
        font_regular = Font(name="Tahoma", size=10)
        font_bold = Font(name="Tahoma", size=10, bold=True)
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )
        total_border = Border(
            left=Side(style='thin', color='94A3B8'),
            right=Side(style='thin', color='94A3B8'),
            top=Side(style='thin', color='94A3B8'),
            bottom=Side(style='double', color='0F172A')
        )
        fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        fill_total = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

        # -------------------------------------------------------------
        # شیت ۱: شناسنامه و خلاصه وضعیت پیمان
        # -------------------------------------------------------------
        ws_info = wb.active
        ws_info.title = "خلاصه پیمان"
        self._apply_sheet_defaults(ws_info)

        ws_info.merge_cells("A1:D1")
        title_cell = ws_info["A1"]
        title_cell.value = f"شناسنامه و وضعیت مالی {contract.project_name}"
        title_cell.font = Font(name="Tahoma", size=14, bold=True, color="1E3A8A")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_info.row_dimensions[1].height = 35

        contract_fields = [
            ("شماره پیمان:", contract.contract_number),
            ("کارفرما:", contract.client_name),
            ("مهندس مشاور:", contract.consultant_name),
            ("پیمانکار:", contract.contractor_name),
            ("مبلغ اولیه پیمان (ریال):", contract.initial_amount),
            ("سقف ۲۵٪ افزایش موضوع ماده ۲۹ (ریال):", contract.initial_amount * 0.25),
            ("حداکثر سقف مجاز پیمان (ریال):", contract.initial_amount * 1.25),
            ("مدت اولیه پیمان (ماه):", contract.duration_months),
            ("تاریخ شروع پیمان:", contract.start_date),
            ("تاریخ اولیه پایان پیمان:", contract.initial_finish_date),
            ("تمدید مجاز طبق لایحه (روز):", analysis_results.get("net_justified_delay_days", 0)),
            ("تاریخ جدید مصوب پایان پیمان:", analysis_results.get("new_finish_date", "-")),
            ("وضعیت اجرایی کارگاه:", contract.current_status)
        ]

        for idx, (label, val) in enumerate(contract_fields, start=3):
            c_lbl = ws_info.cell(row=idx, column=1, value=label)
            c_lbl.font = font_bold
            c_lbl.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
            c_lbl.border = thin_border
            c_lbl.alignment = Alignment(horizontal="right", vertical="center")

            c_val = ws_info.cell(row=idx, column=2, value=val)
            c_val.font = font_regular
            c_val.border = thin_border
            c_val.alignment = Alignment(horizontal="left", vertical="center")

            if isinstance(val, (int, float)) and "ریال" in label:
                c_val.number_format = "#,##0"

            ws_info.row_dimensions[idx].height = 22

        self._auto_fit_columns(ws_info, 3)

        # -------------------------------------------------------------
        # شیت ۲: محاسبات ۵۰۹۰ با فرمول‌های زنده اکسل
        # -------------------------------------------------------------
        ws_5090 = wb.create_sheet(title="محاسبات ۵۰۹۰ تاخیرات")
        self._apply_sheet_defaults(ws_5090)

        ws_5090.merge_cells("A1:K1")
        ws_5090["A1"].value = "جدول رسمی محاسبه تاخیرات ناشی از دیرکرد در پرداخت‌ها (بخشنامه شماره ۵۰۹۰ سازمان برنامه و بودجه)"
        ws_5090["A1"].font = Font(name="Tahoma", size=13, bold=True, color="1E3A8A")
        ws_5090["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws_5090.row_dimensions[1].height = 32

        headers_5090 = [
            "ردیف", "عنوان صورت وضعیت / پیش‌پرداخت", "نوع سند",
            "تاریخ تسلیم به مشاور", "مهلت مشاور (۱۰ روز)", "تاریخ تایید مشاور",
            "مهلت کارفرما (۱۰ روز)", "تاریخ پرداخت واقعی",
            "مبلغ کارکرد/پرداختی F (ریال)", "تاخیر پرداخت D (روز)", "تاخیر مجاز T (روز)"
        ]
        row_h = 3
        for col_idx, h_text in enumerate(headers_5090, start=1):
            ws_5090.cell(row=row_h, column=col_idx, value=h_text)
        self._style_header_row(ws_5090, row_h, len(headers_5090), fill_color="1E3A8A")

        certs = analysis_results.get("processed_certificates", [])
        data_start_row = 4
        for idx, c in enumerate(certs, start=1):
            cur_row = data_start_row + idx - 1
            ws_5090.cell(row=cur_row, column=1, value=idx)
            ws_5090.cell(row=cur_row, column=2, value=c.cert_number)
            ws_5090.cell(row=cur_row, column=3, value="پیش‌پرداخت" if c.cert_type == "advance" else "کارکرد موقت")
            ws_5090.cell(row=cur_row, column=4, value=c.submission_date)
            ws_5090.cell(row=cur_row, column=5, value=c.submission_date)  # نمایش موعد
            ws_5090.cell(row=cur_row, column=6, value=c.consultant_approval_date or "-")
            ws_5090.cell(row=cur_row, column=7, value=c.delay_start_date or "-")
            ws_5090.cell(row=cur_row, column=8, value=c.client_payment_date or "واریز نشده")

            # مبلغ F
            amt_cell = ws_5090.cell(row=cur_row, column=9, value=c.paid_amount if c.paid_amount > 0 else c.approved_amount)
            amt_cell.number_format = "#,##0"

            # تاخیر D (روز)
            ws_5090.cell(row=cur_row, column=10, value=c.total_delay_days)

            # تاخیر مجاز T (فرمول اکسل زنده بر مبنای مبلغ پیمان در شیت ۱)
            # T = (D * F) / P
            f_col = "I"
            d_col = "J"
            # فرمول زنده: =(D * F) / 'خلاصه پیمان'!$B$7
            formula_t = f"=ROUND(({d_col}{cur_row} * {f_col}{cur_row}) / 'خلاصه پیمان'!$B$7, 2)"
            t_cell = ws_5090.cell(row=cur_row, column=11, value=formula_t)
            t_cell.number_format = "0.00"

            # استایل سطر
            bg = fill_zebra if idx % 2 == 0 else PatternFill(fill_type=None)
            for c_idx in range(1, 12):
                cell = ws_5090.cell(row=cur_row, column=c_idx)
                if bg.fill_type:
                    cell.fill = bg
                cell.font = font_regular
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center" if c_idx in [1, 3, 4, 5, 6, 7, 8, 10, 11] else "right", vertical="center")

            ws_5090.row_dimensions[cur_row].height = 22

        # ردیف جمع کل
        tot_row = data_start_row + len(certs)
        ws_5090.cell(row=tot_row, column=2, value="جمع کل کارکرد و تاخیرات ۵۰۹۰")
        ws_5090.cell(row=tot_row, column=2).font = font_bold
        ws_5090.cell(row=tot_row, column=9, value=f"=SUM(I{data_start_row}:I{tot_row-1})").number_format = "#,##0"
        ws_5090.cell(row=tot_row, column=10, value=f"=SUM(J{data_start_row}:J{tot_row-1})")
        ws_5090.cell(row=tot_row, column=11, value=f"=SUM(K{data_start_row}:K{tot_row-1})").number_format = "0.00"

        for col_idx in range(1, 12):
            c = ws_5090.cell(row=tot_row, column=col_idx)
            c.fill = fill_total
            c.font = font_bold
            c.border = total_border
            c.alignment = Alignment(horizontal="center" if col_idx != 2 else "right", vertical="center")
        ws_5090.row_dimensions[tot_row].height = 26

        self._auto_fit_columns(ws_5090, 11)

        # -------------------------------------------------------------
        # شیت ۳: موانع فیزیکی و معارضات جبهه‌های کاری (ماده ۲۸)
        # -------------------------------------------------------------
        ws_ev = wb.create_sheet(title="معارضات و موانع کارگاهی")
        self._apply_sheet_defaults(ws_ev)

        ws_ev.merge_cells("A1:G1")
        ws_ev["A1"].value = "جدول رصد موانع کارگاهی، معارضین تأسیساتی/ملکی و توقفات اجرایی خط ۱۰ (ماده ۲۸ نشریه ۴۳۱۱)"
        ws_ev["A1"].font = Font(name="Tahoma", size=13, bold=True, color="0F766E")
        ws_ev["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws_ev.row_dimensions[1].height = 32

        headers_ev = ["ردیف", "جبهه کاری / ایستگاه / شفت", "نوع معارض", "تاریخ شروع مانع", "تاریخ رفع مانع", "مدت توقف (روز)", "شماره نامه اعلام پیمانکار"]
        for col_idx, h_text in enumerate(headers_ev, start=1):
            ws_ev.cell(row=3, column=col_idx, value=h_text)
        self._style_header_row(ws_ev, 3, len(headers_ev), fill_color="0F766E")

        events = analysis_results.get("processed_events", [])
        for idx, ev in enumerate(events, start=1):
            cur_row = 3 + idx
            ws_ev.cell(row=cur_row, column=1, value=idx)
            ws_ev.cell(row=cur_row, column=2, value=ev.station_or_shaft)
            ws_ev.cell(row=cur_row, column=3, value=ev.event_type)
            ws_ev.cell(row=cur_row, column=4, value=ev.start_date)
            ws_ev.cell(row=cur_row, column=5, value=ev.end_date or "تاکنون رفع نشده")
            ws_ev.cell(row=cur_row, column=6, value=ev.delay_days)
            ws_ev.cell(row=cur_row, column=7, value=ev.official_letter_ref or "-")

            for col_idx in range(1, 8):
                cell = ws_ev.cell(row=cur_row, column=col_idx)
                cell.font = font_regular
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3, 4, 5, 6] else "right", vertical="center")
            ws_ev.row_dimensions[cur_row].height = 22

        self._auto_fit_columns(ws_ev, 7)

        # -------------------------------------------------------------
        # شیت ۴: تضامین و ضمانت‌نامه‌ها
        # -------------------------------------------------------------
        ws_guar = wb.create_sheet(title="تضامین و ضمانت‌نامه‌ها")
        self._apply_sheet_defaults(ws_guar)

        ws_guar.merge_cells("A1:G1")
        ws_guar["A1"].value = "جدول کنترل و سررسید ضمانت‌نامه‌های بانکی پیمان خط ۱۰ مترو"
        ws_guar["A1"].font = Font(name="Tahoma", size=13, bold=True, color="374151")
        ws_guar["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws_guar.row_dimensions[1].height = 32

        headers_guar = ["ردیف", "نوع ضمانت‌نامه", "بانک عامل و شعبه", "شماره ضمانت‌نامه", "مبلغ ضمانت‌نامه (ریال)", "تاریخ صدور", "تاریخ سررسید"]
        for col_idx, h_text in enumerate(headers_guar, start=1):
            ws_guar.cell(row=3, column=col_idx, value=h_text)
        self._style_header_row(ws_guar, 3, len(headers_guar), fill_color="374151")

        for idx, g in enumerate(guarantees, start=1):
            cur_row = 3 + idx
            ws_guar.cell(row=cur_row, column=1, value=idx)
            ws_guar.cell(row=cur_row, column=2, value=g.guarantee_type)
            ws_guar.cell(row=cur_row, column=3, value=g.bank_name)
            ws_guar.cell(row=cur_row, column=4, value=g.guarantee_number)
            c_amt = ws_guar.cell(row=cur_row, column=5, value=g.amount)
            c_amt.number_format = "#,##0"
            ws_guar.cell(row=cur_row, column=6, value=g.issue_date)
            ws_guar.cell(row=cur_row, column=7, value=g.expiry_date)

            for col_idx in range(1, 8):
                cell = ws_guar.cell(row=cur_row, column=col_idx)
                cell.font = font_regular
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center" if col_idx in [1, 2, 4, 6, 7] else "right", vertical="center")
            ws_guar.row_dimensions[cur_row].height = 22

        self._auto_fit_columns(ws_guar, 7)

        full_path = os.path.join(self.output_dir, filename)
        wb.save(full_path)
        return full_path
