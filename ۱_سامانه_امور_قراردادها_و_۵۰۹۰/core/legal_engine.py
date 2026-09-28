"""
موتور دانشنامه حقوقی و مهندسی ادعای امور قراردادها
بازیابی استنادات نشریه ۴۳۱۱، بخشنامه ۵۰۹۰ و تولید متون ادعایی
"""
import os
import json
from typing import List, Dict, Any, Optional


class LegalEngine:
    """موتور تحلیل قوانین و بخشنامه‌ها"""

    def __init__(self, data_path: Optional[str] = None):
        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "knowledge_base.json")
        self.data_path = data_path
        self.knowledge = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"circulars": [], "articles_4311": []}

    def get_article(self, article_num: int) -> Optional[Dict[str, Any]]:
        """دریافت متن و تحلیل یک ماده از شرایط عمومی پیمان"""
        for art in self.knowledge.get("articles_4311", []):
            if art.get("article_number") == article_num:
                return art
        return None

    def get_circular(self, circ_id: str) -> Optional[Dict[str, Any]]:
        """دریافت بخشنامه بر اساس شناسه"""
        for circ in self.knowledge.get("circulars", []):
            if circ.get("id") == circ_id or circ.get("number") == circ_id:
                return circ
        return None

    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """جستجوی هوشمند در متن بخشنامه‌ها و مواد قانونی"""
        q = query.strip().lower()
        results = []

        # جستجو در مواد شرایط عمومی پیمان
        for art in self.knowledge.get("articles_4311", []):
            combined = f"ماده {art.get('article_number')} {art.get('title')} {art.get('description')} {art.get('text')} {art.get('claim_basis')}".lower()
            if q in combined:
                results.append({
                    "type": "شرایط عمومی پیمان (نشریه ۴۳۱۱)",
                    "title": f"ماده {art.get('article_number')}: {art.get('title')}",
                    "content": art.get("text"),
                    "claim_basis": art.get("claim_basis")
                })

        # جستجو در بخشنامه‌ها
        for circ in self.knowledge.get("circulars", []):
            combined = f"{circ.get('title')} {circ.get('summary')} {circ.get('number')} {circ.get('category')}".lower()
            if q in combined:
                results.append({
                    "type": "بخشنامه و دستورالعمل",
                    "title": circ.get("title"),
                    "content": circ.get("summary"),
                    "details": circ.get("key_clauses", [])
                })

        return results

    def build_claim_argument(self, claim_type: str, context: Dict[str, Any]) -> str:
        """
        تولید متن ادعای حقوقی مستند و قوی جهت درج در مکاتبات یا لوایح
        """
        if claim_type == "payment_delay":
            art37 = self.get_article(37)
            art30 = self.get_article(30)
            circ5090 = self.get_circular("circ_5090")
            return (
                f"نظر به اینکه صورت‌وضعیت شماره {context.get('cert_number', '...')} در تاریخ {context.get('submission_date', '...')} "
                f"تسلیم مهندس مشاور گردیده و با عنایت به مواعد مقرر قانونی موضوع ماده ۳۷ شرایط عمومی پیمان (۱۰ روز مهلت بررسی مهندس مشاور "
                f"و ۱۰ روز مهلت تادیه وجه توسط کارفرمای محترم)، متاسفانه واریز مطالبات تا تاریخ {context.get('payment_date', 'حاضر')} "
                f"به تعویق افتاده و منجر به {context.get('delay_days', 0)} روز تاخیر گردیده است؛ لذا به استناد بند (ج) ماده ۳۰ شرایط عمومی "
                f"پیمان (نشریه ۴۳۱۱) و مفاد مصرح در بخشنامه شماره {circ5090.get('number')} سازمان برنامه و بودجه کشور، مدت مذکور بر اساس "
                f"فرمول مصوب T=(D*F)/P معادل {context.get('t_days', 0)} روز تقویمی به عنوان تاخیر مجاز پیمانکار محسوب و به مدت پیمان افزوده خواهد شد."
            )
        elif claim_type == "utility_obstacle":
            art28 = self.get_article(28)
            art30 = self.get_article(30)
            return (
                f"احتراماً پیرو مشاهدات میدانی در جبهه کاری {context.get('site_name', '...')}، به استحضار می‌رساند به علت وقوع "
                f"معارض {context.get('obstacle_type', 'تأسیساتی/ملکی')} شامل {context.get('description', '...')}, "
                f"امکان استقرار تجهیزات، پیشروی ماشین‌آلات حفاری TBM و اجرای سازه ایستگاه از تاریخ {context.get('start_date', '...')} "
                f"سلب گردیده است. با عنایت به مفاد صریح ماده ۲۸ شرایط عمومی پیمان مبنی بر تعهد کارفرمای محترم در تحویل کارگاه و رفع هرگونه "
                f"معارض فیزیکی، تاسیساتی و حقوقی، تاخیرات حاصله ناشی از عدم رفع به موقع مانع مذکور خارج از حیطه قصور پیمانکار بوده و به استناد "
                f"ماده ۳۰ پیمان، کلیه روزهای توقف به عنوان تاخیرات مجاز شناسایی و هزینه‌های بالاسری و استهلاک تجهیزات متوقف مطالبه می‌گردد."
            )
        elif claim_type == "ceiling_25_percent":
            art29 = self.get_article(29)
            return (
                f"احتراماً با عنایت به احجام عملیات اجرایی، دستورکارهای ابلاغی و صورت‌وضعیت‌های کارکرد صادره در خط ۱۰ متروی تهران، "
                f"به آگاهی می‌رساند سقف مالی پیمان به میزان {context.get('used_percent', 0):.1f} درصد از مبلغ اولیه محقق گردیده و پروژه در آستانه "
                f"تکمیل سقف مجاز افزایش ۲۵ درصدی موضوع ماده ۲۹ شرایط عمومی پیمان (نشریه ۴۳۱۱) قرار گرفته است. لذا خواهشمند است به منظور "
                f"پیشگیری از هرگونه وقفه در جبهه‌های کاری و تداوم بهینه عملیات اجرایی TBM، دستور فرمایید تمهیدات لازم جهت انعقاد الحاقیه متمم "
                f"پیمان یا تعیین تکلیف ساختار مالی پروژه مبذول گردد."
            )
        return "متن ادعای عمومی بر اساس شرایط عمومی پیمان."
