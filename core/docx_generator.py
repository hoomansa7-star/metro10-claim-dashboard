"""
موتور تولید اسناد رسمی، لوایح و مکاتبات قراردادی در قالب Word (.docx)
ویژه پروژه خط ۱۰ متروی تهران - قرارگاه سازندگی خاتم‌الانبیاء
با رعایت کامل استایل‌های راست‌به‌چپ (RTL)، جدول‌بندی رسمی و ادبیات اداری فاخر
"""
import os
from typing import Dict, Any, List, Optional
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

from core.jalali import JalaliDate
from core.models import ContractInfo, PaymentCertificate, WorkFrontEvent, Guarantee


def set_cell_background(cell, hex_color: str):
    """تنظیم رنگ پس‌زمینه سلول جدول"""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_paragraph_rtl(p):
    """تنظیم جهت پاراگراف به راست‌به‌چپ (RTL)"""
    pPr = p._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    bidi.set(qn('w:val'), '1')
    pPr.append(bidi)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def format_run(run, font_name="B Nazanin", size_pt=12, bold=False, color_rgb=RGBColor(30, 41, 59)):
    """فرمت‌دهی قلم و اندازه و رنگ متن"""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.font.color.rgb = color_rgb
    # تنظیم قلم برای خط فارسی در XML
    rPr = run._r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    rPr.append(rFonts)


class DocxGenerator:
    """سازنده اسناد رسمی امور قراردادها"""

    def __init__(self, output_dir: Optional[str] = None):
        if not output_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(base_dir, "output_documents")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _create_base_doc(self) -> Document:
        doc = Document()
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.right_margin = Inches(0.9)
            section.left_margin = Inches(0.9)
        return doc

    def _add_header_box(self, doc: Document, contract: ContractInfo, doc_title: str, doc_subtitle: str):
        """افزودن سربرگ سازمانی قرارگاه خاتم‌الانبیاء و پروژه خط ۱۰"""
        p_top = doc.add_paragraph()
        set_paragraph_rtl(p_top)
        p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p_top.add_run("«بسمه تعالی»\n")
        format_run(r1, "B Titr", 12, bold=True)
        r2 = p_top.add_run(f"{contract.contractor_name}\n")
        format_run(r2, "B Titr", 14, bold=True, color_rgb=RGBColor(15, 23, 42))
        r3 = p_top.add_run(f"مدیریت امور قراردادها و دعاوی حقوقی — {contract.project_name}\n")
        format_run(r3, "B Nazanin", 11, bold=True, color_rgb=RGBColor(71, 85, 105))

        # خط جداکننده افقی
        p_line = doc.add_paragraph()
        set_paragraph_rtl(p_line)
        p_line.paragraph_format.space_after = Pt(12)

        # عنوان سند
        p_title = doc.add_paragraph()
        set_paragraph_rtl(p_title)
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_title = p_title.add_run(f"{doc_title}\n")
        format_run(r_title, "B Titr", 16, bold=True, color_rgb=RGBColor(30, 58, 138))
        if doc_subtitle:
            r_sub = p_title.add_run(f"{doc_subtitle}\n")
            format_run(r_sub, "B Nazanin", 12, bold=False, color_rgb=RGBColor(100, 116, 139))

    def generate_delay_claim_document(
        self,
        contract: ContractInfo,
        analysis_results: Dict[str, Any],
        filename: str = "لایحه_جامع_تاخیرات_خط۱۰_مترو.docx"
    ) -> str:
        """
        تولید دفترچه لایحه جامع تاخیرات مجاز ۵۰۹۰ و تاخیرات فنی جبهه‌های کاری خط ۱۰
        """
        doc = self._create_base_doc()
        self._add_header_box(
            doc, contract,
            doc_title="لایحه کارشناسی تمدید مدت پیمان و تاخیرات مجاز",
            doc_subtitle=f"موضوع: پیمان شماره {contract.contract_number} خط ۱۰ متروی تهران — استناد به نشریه ۴۳۱۱ و بخشنامه ۵۰۹۰"
        )

        # ۱. مشخصات قرارداد
        p_h1 = doc.add_paragraph()
        set_paragraph_rtl(p_h1)
        format_run(p_h1.add_run("۱. شناسنامه و مشخصات اجمالی پیمان"), "B Titr", 13, bold=True, color_rgb=RGBColor(30, 58, 138))

        tbl_info = doc.add_table(rows=5, cols=2)
        tbl_info.alignment = WD_TABLE_ALIGNMENT.CENTER
        info_data = [
            ("عنوان پروژه و پیمان:", contract.project_name),
            ("شماره و تاریخ ابلاغ پیمان:", f"{contract.contract_number} مورخ {contract.contract_date}"),
            ("کارفرما / مهندس مشاور:", f"{contract.client_name} / {contract.consultant_name}"),
            ("مبلغ اولیه پیمان:", f"{contract.initial_amount:,.0f} {contract.currency}"),
            ("مدت اولیه و تاریخ‌های پیمان:", f"{contract.duration_months} ماه — شروع: {contract.start_date} لغایت {contract.initial_finish_date}")
        ]
        for row_idx, (k, v) in enumerate(info_data):
            c0, c1 = tbl_info.rows[row_idx].cells
            set_cell_background(c0, "F1F5F9")
            p0 = c0.paragraphs[0]
            set_paragraph_rtl(p0)
            format_run(p0.add_run(k), "B Nazanin", 11, bold=True)
            p1 = c1.paragraphs[0]
            set_paragraph_rtl(p1)
            format_run(p1.add_run(v), "B Nazanin", 11)

        # ۲. مبانی حقوقی و استنادات قانونی
        p_h2 = doc.add_paragraph()
        set_paragraph_rtl(p_h2)
        p_h2.paragraph_format.space_before = Pt(14)
        format_run(p_h2.add_run("۲. مبانی حقوقی و بخشنامه‌های حاکم بر لایحه"), "B Titr", 13, bold=True, color_rgb=RGBColor(30, 58, 138))

        p_legal = doc.add_paragraph()
        set_paragraph_rtl(p_legal)
        text_legal = (
            "این لایحه بر مبنای حقوق مکتسبه پیمانکار و به استناد بندهای صریح شرایط عمومی پیمان (نشریه ۴۳۱۱) "
            "و دستورالعمل‌های نظام فنی و اجرایی کشور تنظیم گردیده است:\n"
            "الف) ماده ۳۰ شرایط عمومی پیمان (تغییر مدت پیمان): هرگاه به علت تاخیر در پرداخت صورت‌وضعیت‌ها، "
            "عدم تحویل یا رفع معارض جبهه‌های کاری، یا تغییرات فنی عملیات، کار متوقف یا کند شود، مدت پیمان تمدید خواهد شد.\n"
            "ب) بخشنامه شماره ۵۰۹۰/۵۴-۲۴۹۰/۱۰۵ سازمان برنامه و بودجه کشور: ناظر بر نحوه محاسبه تاخیرات مجاز ناشی از "
            "تاخیر در پرداخت صورت‌وضعیت‌ها بر مبنای رابطه T=(D*F)/P.\n"
            "ج) ماده ۲۸ شرایط عمومی پیمان: تعهد صریح کارفرما در خصوص تحویل بی‌قید و شرط اراضی شفت‌ها، کارگاه‌ها و رفع معارضین."
        )
        format_run(p_legal.add_run(text_legal), "B Nazanin", 11)

        # ۳. جدول تفصیلی محاسبات بخشنامه ۵۰۹۰ (تاخیرات مالی)
        p_h3 = doc.add_paragraph()
        set_paragraph_rtl(p_h3)
        p_h3.paragraph_format.space_before = Pt(14)
        format_run(p_h3.add_run("۳. جدول محاسبات تاخیرات مالی بر اساس بخشنامه ۵۰۹۰"), "B Titr", 13, bold=True, color_rgb=RGBColor(30, 58, 138))

        certs = analysis_results.get("processed_certificates", [])
        tbl_certs = doc.add_table(rows=len(certs) + 1, cols=6)
        tbl_certs.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers_cert = ["شرح صورت وضعیت", "تاریخ تسلیم", "تاریخ پرداخت", "مبلغ پرداختی (ریال)", "تاخیر D (روز)", "تاخیر مجاز T (روز)"]
        for col_idx, h_text in enumerate(headers_cert):
            cell = tbl_certs.rows[0].cells[col_idx]
            set_cell_background(cell, "1E3A8A")
            p = cell.paragraphs[0]
            set_paragraph_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            format_run(p.add_run(h_text), "B Titr", 10, bold=True, color_rgb=RGBColor(255, 255, 255))

        for row_idx, c in enumerate(certs, start=1):
            row_cells = tbl_certs.rows[row_idx].cells
            vals = [
                c.cert_number,
                c.submission_date or "-",
                c.client_payment_date or "پرداخت نشده",
                f"{c.paid_amount:,.0f}" if c.paid_amount > 0 else f"{c.approved_amount:,.0f}",
                str(c.total_delay_days),
                f"{c.justified_delay_days:.2f}"
            ]
            bg_col = "FFFFFF" if row_idx % 2 == 1 else "F8FAFC"
            for col_idx, val in enumerate(vals):
                cell = row_cells[col_idx]
                set_cell_background(cell, bg_col)
                p = cell.paragraphs[0]
                set_paragraph_rtl(p)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [1, 2, 4, 5] else WD_ALIGN_PARAGRAPH.RIGHT
                format_run(p.add_run(val), "B Nazanin", 10)

        # ۴. جدول موانع فیزیکی و معارضات جبهه‌های کاری (ماده ۲۸)
        p_h4 = doc.add_paragraph()
        set_paragraph_rtl(p_h4)
        p_h4.paragraph_format.space_before = Pt(14)
        format_run(p_h4.add_run("۴. موانع فیزیکی، تاسیساتی و معارضات کارگاهی (ماده ۲۸ شرایط عمومی پیمان)"), "B Titr", 13, bold=True, color_rgb=RGBColor(30, 58, 138))

        events = analysis_results.get("processed_events", [])
        tbl_events = doc.add_table(rows=len(events) + 1, cols=5)
        tbl_events.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers_ev = ["جبهه کاری / ایستگاه", "نوع معارض", "بازه توقف", "روزهای توقف", "شرح معارض و مکاتبه"]
        for col_idx, h_text in enumerate(headers_ev):
            cell = tbl_events.rows[0].cells[col_idx]
            set_cell_background(cell, "0F766E")
            p = cell.paragraphs[0]
            set_paragraph_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            format_run(p.add_run(h_text), "B Titr", 10, bold=True, color_rgb=RGBColor(255, 255, 255))

        for row_idx, ev in enumerate(events, start=1):
            row_cells = tbl_events.rows[row_idx].cells
            vals = [
                ev.station_or_shaft,
                ev.event_type,
                f"از {ev.start_date} تا {ev.end_date or 'جاری'}",
                str(ev.delay_days),
                f"{ev.description} (نامه: {ev.official_letter_ref or '-'})"
            ]
            bg_col = "FFFFFF" if row_idx % 2 == 1 else "F0FDFA"
            for col_idx, val in enumerate(vals):
                cell = row_cells[col_idx]
                set_cell_background(cell, bg_col)
                p = cell.paragraphs[0]
                set_paragraph_rtl(p)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [1, 2, 3] else WD_ALIGN_PARAGRAPH.RIGHT
                format_run(p.add_run(val), "B Nazanin", 10)

        # ۵. جمع‌بندی تحلیل همپوشانی و درخواست تمدید مدت پیمان
        p_h5 = doc.add_paragraph()
        set_paragraph_rtl(p_h5)
        p_h5.paragraph_format.space_before = Pt(14)
        format_run(p_h5.add_run("۵. تحلیل همپوشانی (Overlap) و نتیجه‌گیری تمدید مجاز پیمان"), "B Titr", 13, bold=True, color_rgb=RGBColor(30, 58, 138))

        p_res = doc.add_paragraph()
        set_paragraph_rtl(p_res)
        summary_text = (
            f"با اجرای تحلیل دقیق همپوشانی میان تاخیرات مالی ۵۰۹۰ و توقفات ناشی از معارضات فیزیکی:\n"
            f"• مجموع جبری ایام تاخیر مالی بخشنامه ۵۰۹۰: {analysis_results.get('raw_financial_t_sum', 0)} روز تقویمی\n"
            f"• مجموع روزهای موانع فنی و معارضین جبهه‌های کاری: {analysis_results.get('raw_technical_days_sum', 0)} روز تقویمی\n"
            f"• ایام همپوشانی (تداخل روزهای مالی و فنی): {analysis_results.get('overlap_days_count', 0)} روز\n"
            f"• خالص تاخیرات مجاز تقویمی (بدون دوباره‌شماری): {analysis_results.get('net_justified_delay_days', 0)} روز تقویمی (معادل {analysis_results.get('extension_months', 0)} ماه)\n"
            f"• تاریخ پایان اولیه پیمان: {analysis_results.get('initial_finish_date')}\n"
            f"• تاریخ مجاز جدید پایان پیمان پس از اعمال تمدید: {analysis_results.get('new_finish_date')}\n\n"
            "لذا خواهشمند است دستور فرمایید مراتب تمدید مدت پیمان به میزان فوق ابلاغ و از اعمال هرگونه خسارت تاخیرات به حساب پیمانکار خودداری گردد."
        )
        format_run(p_res.add_run(summary_text), "B Nazanin", 11, bold=True)

        # امضاها
        p_sign = doc.add_paragraph()
        set_paragraph_rtl(p_sign)
        p_sign.paragraph_format.space_before = Pt(30)
        p_sign.alignment = WD_ALIGN_PARAGRAPH.CENTER
        format_run(p_sign.add_run(f"با احترام و تشکر\n{contract.contractor_name}\nمدیریت پروژه خط ۱۰ مترو تهران"), "B Titr", 12, bold=True)

        full_path = os.path.join(self.output_dir, filename)
        doc.save(full_path)
        return full_path

    def generate_claim_letter(
        self,
        contract: ContractInfo,
        letter_type: str,
        context: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        تولید نامه‌های رسمی ادعایی خط ۱۰ مترو (ماده ۳۷ پرداخت‌ها، ماده ۲۸ معارضین، ماده ۲۹ سقف ۲۵٪)
        """
        doc = self._create_base_doc()
        today_j = JalaliDate.today_jalali()

        letter_configs = {
            "payment_delay": {
                "title": "اعلام تاخیر در پرداخت صورت وضعیت و مطالبه تمدید مدت و خسارت افت راندمان",
                "default_file": "نامه_ادعایی_تاخیر_پرداخت_ماده۳۷.docx",
                "to": f"جناب آقای مهندس مشاور پروژه خط ۱۰ مترو تهران ({contract.consultant_name})\nرونوشت: مدیریت محترم شرکت راه‌آهن شهری تهران و حومه (مترو)",
                "subject": f"موضوع: تاخیر در پرداخت مطالبات و صورت‌وضعیت شماره {context.get('cert_number', '...')} — پیمان {contract.contract_number}",
                "body": (
                    f"با صلوات بر محمد و آل محمد (ص)،\n"
                    f"احتراماً پیرو تسلیم صورت‌وضعیت شماره {context.get('cert_number', '...')} در تاریخ {context.get('submission_date', '...')} "
                    f"به مبلغ ناخالص {float(context.get('amount', 0)):,.0f} ریال، به استحضار می‌رساند علیرغم انقضای مواعد مصرح در ماده ۳۷ "
                    f"شرایط عمومی پیمان (نشریه ۴۳۱۱) شامل مهلت ۱۰ روزه بررسی مهندس مشاور و ۱۰ روزه پرداخت توسط کارفرمای محترم، متاسفانه "
                    f"تاکنون وجوه مربوطه پرداخت نگردیده و منجر به ایجاد وقفه مالی در زنجیره تامین مصالح و تولید سگمنت‌های بتنی شده است.\n\n"
                    f"با عنایت به اینکه تاخیر به وقوع پیوسته موجب افت محسوس راندمان ماشین‌آلات مکانیزه TBM و کاهش بهره‌وری نیروی انسانی مستقر در "
                    f"شفت‌ها و ایستگاه‌ها گردیده است، بدینوسیله به استناد بند (ج) ماده ۳۰ شرایط عمومی پیمان و بخشنامه شماره ۵۰۹۰ سازمان برنامه و بودجه، "
                    f"مراتب به عنوان تاخیرات مجاز مالی ثبت گردیده و حق مطالبه خسارات ناشی از افزایش هزینه‌های بالاسری کارگاه برای این پیمانکار محفوظ است.\n\n"
                    f"خواهشمند است دستور فرمایید به منظور جلوگیری از توقف عملیات اجرایی خط ۱۰، در تسریع در پرداخت مطالبات تسریع لازم معمول فرمایند."
                )
            },
            "utility_obstacle": {
                "title": "اعلام وقوع معارض فیزیکی/تاسیساتی و توقف عملیات اجرایی جبهه کاری",
                "default_file": "نامه_رسمی_معارض_شفت_ایستگاه_ماده۲۸.docx",
                "to": f"جناب آقای مهندس مشاور پروژه خط ۱۰ مترو تهران ({contract.consultant_name})\nرونوشت: مدیر محترم مجری خط ۱۰ شرکت مترو تهران",
                "subject": f"موضوع: توقف کارگاه ناشی از وقوع معارض در {context.get('site_name', 'شفت/ایستگاه')} — پیمان {contract.contract_number}",
                "body": (
                    f"با صلوات بر محمد و آل محمد (ص)،\n"
                    f"احتراماً به استحضار می‌رساند در ادامه عملیات اجرایی در جبهه کاری {context.get('site_name', '...')}، "
                    f"به دلیل برخورد با {context.get('obstacle_desc', 'معارض تاسیساتی لوله گاز/کابل برق/تملک زمین')}، "
                    f"عملیات حفاری و استقرار ماشین‌آلات از تاریخ {context.get('start_date', '...')} با بن‌بست اجرایی مواجه گردیده است.\n\n"
                    f"همانگونه که مستحضرید وفق ماده ۲۸ شرایط عمومی پیمان، تحویل جبهه‌های کاری عاری از هرگونه معارض و تامین دسترسی کامل کارگاهی از وظایف "
                    f"ذاتی کارفرمای محترم می‌باشد. با عنایت به اینکه جبهه مذکور بر روی مسیر بحرانی پروژه واقع است، تداوم این توقف منجر به بیکاری "
                    f"نیروها و استهلاک تجهیزات سنگین مستقر خواهد شد.\n\n"
                    f"لذا خواهشمند است دستور فرمایید نسبت به هماهنگی با ارگان‌های ذیربط جهت جابجایی و رفع فوری معارض اقدام مقتضی صورت پذیرد. "
                    f"بدیهی است کلیه روزهای توقف کارگاه وفق ماده ۳۰ پیمان به عنوان تاخیر مجاز تلقی شده و لایحه خسارت متناظر متعاقباً ارسال خواهد شد."
                )
            },
            "ceiling_25_percent": {
                "title": "هشدار رسیدن به سقف ۲۵٪ ماده ۲۹ و درخواست ابلاغ الحاقیه پیمان",
                "default_file": "نامه_هشدار_سقف۲۵درصد_ماده۲۹.docx",
                "to": f"مدیریت محترم عامل شرکت راه‌آهن شهری تهران و حومه (مترو)\nرونوشت: مهندسین مشاور پروژه خط ۱۰",
                "subject": f"موضوع: اتمام سقف ۲۵٪ افزایش مبلغ موضوع ماده ۲۹ شرایط عمومی پیمان — پیمان {contract.contract_number}",
                "body": (
                    f"با صلوات بر محمد و آل محمد (ص)،\n"
                    f"احتراماً پیرو اجرای دستورکارهای ابلاغی، احجام تغییر یافته در پروفیل مسیر تونل و کارهای جدید ایجاد شده در ایستگاه‌های خط ۱۰، "
                    f"به استحضار می‌رساند مجموع کارکردهای قطعی و برآوردی صادره، از سقف ۲۵ درصد افزایش مبلغ اولیه پیمان مندرج در ماده ۲۹ "
                    f"شرایط عمومی پیمان عبور نموده و ادامه عملیات مستلزم بازنگری حقوقی در ساختار قرارداد می‌باشد.\n\n"
                    f"از آنجا که مطابق ضوابط سازمان برنامه و بودجه و شرایط عمومی پیمان، ادامه کار فراتر از سقف قانونی ۲۵٪ نیازمند تعیین تکلیف، "
                    f"تنظیم متمم و ابلاغ الحاقیه رسمی است، خواهشمند است دستور فرمایید کمیته مشترکی جهت ارزیابی احجام باقی‌مانده و تنظیم پیش‌نویس "
                    f"الحاقیه پیمان تشکیل گردد تا مانعی در تداوم حرکت دستگاه TBM و برنامه‌ریزی قطعه غربی خط ۱۰ مترو ایجاد نشود."
                )
            }
        }

        cfg = letter_configs.get(letter_type, letter_configs["payment_delay"])
        fn = filename or cfg["default_file"]

        self._add_header_box(
            doc, contract,
            doc_title=cfg["title"],
            doc_subtitle=f"تاریخ تنظیم: {today_j} — پیوست دارد"
        )

        p_to = doc.add_paragraph()
        set_paragraph_rtl(p_to)
        format_run(p_to.add_run(cfg["to"]), "B Titr", 11, bold=True)

        p_sub = doc.add_paragraph()
        set_paragraph_rtl(p_sub)
        p_sub.paragraph_format.space_before = Pt(8)
        format_run(p_sub.add_run(cfg["subject"]), "B Nazanin", 12, bold=True)

        p_body = doc.add_paragraph()
        set_paragraph_rtl(p_body)
        p_body.paragraph_format.space_before = Pt(10)
        p_body.paragraph_format.line_spacing = 1.3
        format_run(p_body.add_run(cfg["body"]), "B Nazanin", 12)

        p_sign = doc.add_paragraph()
        set_paragraph_rtl(p_sign)
        p_sign.paragraph_format.space_before = Pt(30)
        p_sign.alignment = WD_ALIGN_PARAGRAPH.CENTER
        format_run(p_sign.add_run(f"با احترام فراوان\nمجری طرح و مدیر پروژه خط ۱۰ متروی تهران\n{contract.contractor_name}"), "B Titr", 12, bold=True)

        full_path = os.path.join(self.output_dir, fn)
        doc.save(full_path)
        return full_path

    def generate_site_minutes(
        self,
        contract: ContractInfo,
        event: WorkFrontEvent,
        filename: Optional[str] = None
    ) -> str:
        """
        تولید صورت‌جلسه کارگاهی ثبت موانع فیزیکی و معارضین خط ۱۰
        """
        doc = self._create_base_doc()
        today_j = JalaliDate.today_jalali()
        fn = filename or f"صورتجلسه_کارگاهی_{event.station_or_shaft.replace(' ', '_')}.docx"

        self._add_header_box(
            doc, contract,
            doc_title="صورت‌جلسه کارگاهی ثبت موانع اجرایی و معارضین جبهه کاری",
            doc_subtitle=f"تاریخ صورت‌جلسه: {today_j} — جبهه کاری: {event.station_or_shaft}"
        )

        p_intro = doc.add_paragraph()
        set_paragraph_rtl(p_intro)
        intro_text = (
            f"در تاریخ {today_j} جلسه مشترکی با حضور نمایندگان ذیصلاح کارفرما ({contract.client_name})، "
            f"مهندس مشاور ({contract.consultant_name}) و پیمانکار ({contract.contractor_name}) در محل کارگاه {event.station_or_shaft} "
            f"برگزار گردید و وضعیت مانع اجرایی به شرح ذیل صورت‌جلسه شد:"
        )
        format_run(p_intro.add_run(intro_text), "B Nazanin", 11)

        tbl = doc.add_table(rows=6, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        fields = [
            ("محل دقیق و جبهه کاری:", event.station_or_shaft),
            ("نوع معارض:", event.event_type),
            ("تاریخ آغاز توقف / مانع:", event.start_date),
            ("تاریخ رفع مانع:", event.end_date or "تاکنون رفع نگردیده است"),
            ("شرح تفصیلی مشاهدات میدانی:", event.description),
            ("تاثیر بر ماشین‌آلات و برنامه زمانی:", "باعث توقف جبهه در مسیر بحرانی و عدم امکان پیشروی TBM")
        ]
        for idx, (lbl, val) in enumerate(fields):
            c0, c1 = tbl.rows[idx].cells
            set_cell_background(c0, "F1F5F9")
            p0 = c0.paragraphs[0]
            set_paragraph_rtl(p0)
            format_run(p0.add_run(lbl), "B Nazanin", 11, bold=True)
            p1 = c1.paragraphs[0]
            set_paragraph_rtl(p1)
            format_run(p1.add_run(val), "B Nazanin", 11)

        # محل امضاها
        p_signs = doc.add_paragraph()
        set_paragraph_rtl(p_signs)
        p_signs.paragraph_format.space_before = Pt(35)
        p_signs.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sig_text = (
            "نماینده مهندس مشاور                   نماینده کارفرما (مترو تهران)                   نماینده پیمانکار (خاتم‌الانبیاء)\n\n"
            "مهر و امضا                           مهر و امضا                                   مهر و امضا"
        )
        format_run(p_signs.add_run(sig_text), "B Titr", 11, bold=True)

        full_path = os.path.join(self.output_dir, fn)
        doc.save(full_path)
        return full_path
