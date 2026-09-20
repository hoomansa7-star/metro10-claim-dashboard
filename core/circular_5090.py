"""
ماژول تخصصی محاسبات بخشنامه ۵۰۹۰ و تحلیل همپوشانی تاخیرات مالی و فنی
سازمان برنامه و بودجه و نشریه ۴۳۱۱ شرایط عمومی پیمان
"""
from typing import List, Dict, Any, Set, Tuple
from datetime import date, timedelta
from core.jalali import JalaliDate
from core.models import PaymentCertificate, WorkFrontEvent, ContractInfo


class Circular5090Engine:
    """موتور محاسباتی بخشنامه ۵۰۹۰ و مهندسی ارزش تاخیرات پیمان"""

    CONSULTANT_DEADLINE_DAYS = 10  # مهلت ۱۰ روزه مهندس مشاور طبق ماده ۳۷
    CLIENT_DEADLINE_DAYS = 10      # مهلت ۱۰ روزه کارفرما طبق ماده ۳۷
    TOTAL_LEGAL_DEADLINE_DAYS = 20 # جمع مهلت قانونی رسیدگی و پرداخت از تسلیم

    @classmethod
    def calculate_certificate(cls, cert: PaymentCertificate, contract_amount: float) -> PaymentCertificate:
        """
        محاسبه تاخیرات یک صورت وضعیت یا پیش‌پرداخت بر اساس بخشنامه ۵۰۹۰
        فرمول: T = (D * F) / P
        """
        if not cert.submission_date:
            return cert

        # ۱. تعیین موعد مقرر پرداخت طبق ماده ۳۷ شرایط عمومی پیمان
        if cert.cert_type == "advance":
            # برای پیش‌پرداخت: موعد پرداخت معمولاً ۱۰ الی ۲۰ روز پس از تسلیم تضمین است
            due_date_str = JalaliDate.add_days_jalali(cert.submission_date, 15)
        else:
            if cert.consultant_approval_date:
                # اگر مشاور در موعد تأیید کرده باشد، مهلت کارفرما ۱۰ روز بعد از تایید مشاور است
                due_date_str = JalaliDate.add_days_jalali(cert.consultant_approval_date, cls.CLIENT_DEADLINE_DAYS)
            else:
                # اگر تاریخ تایید مشاور ثبت نشده، سقف مهلت ۲۰ روز از تاریخ تسلیم پیمانکار ملاک است
                due_date_str = JalaliDate.add_days_jalali(cert.submission_date, cls.TOTAL_LEGAL_DEADLINE_DAYS)

        # ۲. محاسبه روزهای تاخیر در پرداخت (D)
        if cert.client_payment_date:
            delay_d = JalaliDate.days_between(due_date_str, cert.client_payment_date)
            # اگر زودتر واریز شده باشد تاخیر صفر است (تسریع)
            delay_d = max(0, delay_d)
        else:
            # اگر هنوز پرداخت نشده، تاخیر تا تاریخ جاری سیستم محاسبه می‌شود
            today_j = JalaliDate.today_jalali()
            delay_d = max(0, JalaliDate.days_between(due_date_str, today_j))

        cert.total_delay_days = delay_d

        # ۳. محاسبه تاخیر مجاز (T) طبق بخشنامه ۵۰۹۰
        # F: مبلغ تایید شده یا دریافتی دوره
        # P: مبلغ پیمان
        effective_f = cert.paid_amount if cert.paid_amount > 0 else cert.approved_amount
        if contract_amount > 0 and effective_f > 0 and delay_d > 0:
            # فرمول دقیق ۵۰۹۰: T = (D * F) / P
            t_days = (delay_d * effective_f) / contract_amount
            cert.justified_delay_days = round(t_days, 2)
        else:
            cert.justified_delay_days = 0.0

        # بازه زمانی تاخیر برای محاسبات همپوشانی
        cert.delay_start_date = due_date_str
        # بازه مجاز از موعد پرداخت به مدت T روز ادامه می‌یابد
        t_int = int(round(cert.justified_delay_days))
        cert.delay_end_date = JalaliDate.add_days_jalali(due_date_str, t_int)

        return cert

    @classmethod
    def perform_overlap_analysis(
        cls,
        certificates: List[PaymentCertificate],
        events: List[WorkFrontEvent],
        contract: ContractInfo
    ) -> Dict[str, Any]:
        """
        تحلیل جامع همپوشانی (Overlap Analysis) بین تاخیرات مالی (۵۰۹۰) و موانع فنی (ماده ۲۸ و رویدادها)
        جلوگیری از دوباره‌شماری روزها طبق اصول حقوقی و مهندسی ارزش
        """
        financial_days_set: Set[date] = set()
        technical_days_set: Set[date] = set()

        processed_certs = []
        raw_financial_t_sum = 0.0

        # ۱. پردازش صورت‌وضعیت‌ها و پر کردن مجموعه روزهای مالی
        for cert in certificates:
            c = cls.calculate_certificate(cert, contract.initial_amount)
            processed_certs.append(c)
            raw_financial_t_sum += c.justified_delay_days

            if c.delay_start_date and c.delay_end_date and c.justified_delay_days > 0:
                start_d = JalaliDate.parse_jalali_str(c.delay_start_date)
                end_d = JalaliDate.parse_jalali_str(c.delay_end_date)
                if start_d and end_d and end_d >= start_d:
                    cur = start_d
                    while cur <= end_d:
                        financial_days_set.add(cur)
                        cur += timedelta(days=1)

        # ۲. پردازش موانع فنی و معارضات کارگاهی (فقط جبهه‌های موثر بر مسیر بحرانی)
        processed_events = []
        raw_technical_days_sum = 0
        for ev in events:
            if not ev.impact_on_critical_path:
                continue
            start_d = JalaliDate.parse_jalali_str(ev.start_date)
            end_d = JalaliDate.parse_jalali_str(ev.end_date) if ev.end_date else date.today()
            if start_d and end_d and end_d >= start_d:
                ev_days = (end_d - start_d).days + 1
                ev.delay_days = ev_days
                raw_technical_days_sum += ev_days
                processed_events.append(ev)

                cur = start_d
                while cur <= end_d:
                    technical_days_set.add(cur)
                    cur += timedelta(days=1)

        # ۳. محاسبه اشتراک (همپوشانی) و اجتماع روزها (روزهای خالص مجاز)
        union_all_days = financial_days_set.union(technical_days_set)
        overlap_days_set = financial_days_set.intersection(technical_days_set)

        net_justified_delay_days = len(union_all_days)
        overlap_days_count = len(overlap_days_set)
        financial_pure_days = len(financial_days_set)
        technical_pure_days = len(technical_days_set)

        # ۴. محاسبه تاریخ پایان مجاز جدید پیمان
        new_finish_date = JalaliDate.add_days_jalali(contract.initial_finish_date, net_justified_delay_days)

        return {
            "processed_certificates": processed_certs,
            "processed_events": processed_events,
            "raw_financial_t_sum": round(raw_financial_t_sum, 2),
            "raw_technical_days_sum": raw_technical_days_sum,
            "financial_calendar_days": financial_pure_days,
            "technical_calendar_days": technical_pure_days,
            "overlap_days_count": overlap_days_count,
            "net_justified_delay_days": net_justified_delay_days,
            "initial_finish_date": contract.initial_finish_date,
            "new_finish_date": new_finish_date,
            "extension_months": round(net_justified_delay_days / 30.5, 1)
        }
