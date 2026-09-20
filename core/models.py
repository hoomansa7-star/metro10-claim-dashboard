"""
مدل‌های داده‌ای سامانه امور قراردادها و مهندسی ادعا
پروژه خط ۱۰ متروی تهران - قرارگاه سازندگی خاتم‌الانبیاء
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from core.jalali import JalaliDate


class ContractInfo(BaseModel):
    """شناسنامه و مشخصات پایه پیمان"""
    project_name: str = "پروژه احداث خط ۱۰ متروی تهران (قطعه غربی)"
    contract_number: str = "۱۰/م/۱۴۰۱/۹۸۲"
    contract_date: str = "1401/04/15"
    start_date: str = "1401/05/01"
    duration_months: int = 48
    initial_finish_date: str = "1405/05/01"
    initial_amount: float = 15400000000000.0  # ۱۵ هزار و ۴۰۰ میلیارد ریال
    client_name: str = "شرکت راه‌آهن شهری تهران و حومه (مترو)"
    consultant_name: str = "مهندسین مشاور جامع راهور / رهساز طرح"
    contractor_name: str = "قرارگاه سازندگی خاتم‌الانبیاء (ص) - موسسه حرا"
    contract_type: str = "طرح و ساخت (EPC) منضم به نشریه ۴۳۱۱"
    currency: str = "ریال"
    workshop_location: str = "تهران، منطقه ۲۲، دریاچه شهدای خلیج فارس، شفت غربی خط ۱۰"
    current_status: str = "در حال اجرا - عملیات حفاری مکانیزه با دو دستگاه TBM و احداث سازه ایستگاه‌ها"

    @property
    def ceiling_25_percent(self) -> float:
        """سقف افزایش ۲۵ درصدی موضوع ماده ۲۹ شرایط عمومی پیمان"""
        return self.initial_amount * 0.25

    @property
    def max_permissible_amount(self) -> float:
        """حداکثر سقف مبلغ پیمان با احتساب ۲۵ درصد افزایش"""
        return self.initial_amount * 1.25


class PaymentCertificate(BaseModel):
    """صورت‌وضعیت کارکرد، پیش‌پرداخت یا تعدیل"""
    id: str
    cert_number: str
    cert_type: str = "interim"  # advance | interim | adjustment
    period_from: Optional[str] = None
    period_to: Optional[str] = None
    submission_date: str  # تاریخ تسلیم پیمانکار
    consultant_approval_date: Optional[str] = None  # تاریخ تایید مشاور
    client_payment_date: Optional[str] = None  # تاریخ واریز کارفرما
    claimed_amount: float  # مبلغ ناخالص ارسالی پیمانکار
    approved_amount: float  # مبلغ تایید شده مشاور
    paid_amount: float = 0.0  # مبلغ پرداختی واقعی کارفرما
    payment_method: str = "نقدی"  # نقدی | اسناد خزانه اسلامی (اخزا) | تهاتر
    consultant_delay_days: int = 0
    client_delay_days: int = 0
    total_delay_days: int = 0  # D در بخشنامه ۵۰۹۰
    justified_delay_days: float = 0.0  # T در بخشنامه ۵۰۹۰
    delay_start_date: Optional[str] = None
    delay_end_date: Optional[str] = None
    notes: Optional[str] = None


class WorkFrontEvent(BaseModel):
    """رویدادها، موانع فیزیکی و معارضات جبهه‌های کاری خط ۱۰"""
    id: str
    station_or_shaft: str  # نام ایستگاه یا شفت
    event_type: str  # معارض تأسیساتی | معارض ملکی و تحویل زمین | تاخیر نقشه | مجوز ترافیک | سایر
    start_date: str  # تاریخ شروع مانع
    end_date: Optional[str] = None  # تاریخ رفع مانع (در صورت رفع)
    description: str  # شرح مانع
    impact_on_critical_path: bool = True  # تاثیر بر مسیر بحرانی
    delay_days: int = 0  # تعداد روزهای تقویمی توقف
    official_letter_ref: Optional[str] = None  # شماره نامه اعلام پیمانکار
    client_response_ref: Optional[str] = None  # شماره نامه پاسخ کارفرما
    status: str = "در حال پیگیری"  # در حال پیگیری | رفع معارض | متوقف


class Guarantee(BaseModel):
    """ضمانت‌نامه‌های بانکی پیمان"""
    id: str
    guarantee_type: str  # پیش‌پرداخت | حسن انجام تعهدات | استرداد کسور وجه‌الضمان
    bank_name: str
    guarantee_number: str
    amount: float
    issue_date: str
    expiry_date: str
    status: str = "معتبر"  # معتبر | در آستانه انقضا | تمدید شده | آزاد شده


class ProjectDatabase(BaseModel):
    """بانک اطلاعات تجمیعی پروژه"""
    contract: ContractInfo
    certificates: List[PaymentCertificate] = []
    events: List[WorkFrontEvent] = []
    guarantees: List[Guarantee] = []
