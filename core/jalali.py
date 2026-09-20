"""
ماژول مستقل تبدیل تاریخ شمسی (جلالی) و میلادی و محاسبات روزهای تقویمی
بدون وابستگی خارجی برای استفاده در سامانه امور قراردادها
"""
from datetime import date, datetime, timedelta
from typing import Tuple, Optional


class JalaliDate:
    """ابزار محاسبات و تبدیل تاریخ شمسی به میلادی و برعکس بر اساس الگوریتم استاندارد نجومی"""

    @staticmethod
    def gregorian_to_jalali(gy: int, gm: int, gd: int) -> Tuple[int, int, int]:
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        if gy > 1600:
            jy = 979
            gy -= 1600
        else:
            jy = 0
            gy -= 621
        gy2 = gy + 1 if (gm > 2) else gy
        days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
        jy += 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365
        if days < 186:
            jm = 1 + (days // 31)
            jd = 1 + (days % 31)
        else:
            jm = 7 + ((days - 186) // 30)
            jd = 1 + ((days - 186) % 30)
        return jy, jm, jd

    @staticmethod
    def jalali_to_gregorian(jy: int, jm: int, jd: int) -> Tuple[int, int, int]:
        if jy > 979:
            gy = 1600
            jy -= 979
        else:
            gy = 621
        days = (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + 78 + jd
        if jm < 7:
            days += (jm - 1) * 31
        else:
            days += ((jm - 7) * 30) + 186
        gy += 400 * (days // 146097)
        days %= 146097
        if days > 36524:
            days -= 1
            gy += 100 * (days // 36524)
            days %= 36524
            if days >= 365:
                days += 1
        gy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            gy += (days - 1) // 365
            days = (days - 1) % 365
        gd_m = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        # بررسی سال کبیسه میلادی
        if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0):
            gd_m[2] = 29
        gm = 1
        while gm <= 12 and days >= gd_m[gm]:
            days -= gd_m[gm]
            gm += 1
        gd = days + 1
        return gy, gm, gd

    @classmethod
    def parse_jalali_str(cls, date_str: str) -> Optional[date]:
        """تبدیل رشته تاریخ شمسی مانند 1402/06/15 به شیء date میلادی"""
        if not date_str or not isinstance(date_str, str):
            return None
        cleaned = date_str.strip().replace('-', '/').replace('.', '/')
        parts = cleaned.split('/')
        if len(parts) != 3:
            return None
        try:
            jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
            gy, gm, gd = cls.jalali_to_gregorian(jy, jm, jd)
            return date(gy, gm, gd)
        except Exception:
            return None

    @classmethod
    def to_jalali_str(cls, g_date: Optional[date]) -> str:
        """تبدیل شیء date میلادی به رشته تاریخ شمسی فرمت شده YYYY/MM/DD"""
        if not g_date:
            return ""
        jy, jm, jd = cls.gregorian_to_jalali(g_date.year, g_date.month, g_date.day)
        return f"{jy:04d}/{jm:02d}/{jd:02d}"

    @classmethod
    def today_jalali(cls) -> str:
        return cls.to_jalali_str(date.today())

    @classmethod
    def days_between(cls, jalali_start: str, jalali_end: str) -> int:
        """محاسبه اختلاف روز بین دو تاریخ شمسی"""
        d1 = cls.parse_jalali_str(jalali_start)
        d2 = cls.parse_jalali_str(jalali_end)
        if d1 and d2:
            return (d2 - d1).days
        return 0

    @classmethod
    def add_days_jalali(cls, jalali_date_str: str, days: int) -> str:
        """افزودن تعدادی روز به یک تاریخ شمسی"""
        d = cls.parse_jalali_str(jalali_date_str)
        if not d:
            return jalali_date_str
        new_d = d + timedelta(days=days)
        return cls.to_jalali_str(new_d)
