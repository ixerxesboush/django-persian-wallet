import datetime

import jdatetime


def toman_format(amount):
    """Return a whole-Toman amount using thousands separators."""
    return f'{int(amount or 0):,} تومان'


def jalali_to_gregorian(j_year, j_month, j_day):
    """Convert a Jalali date to a Gregorian date."""
    try:
        return jdatetime.date(j_year, j_month, j_day).togregorian()
    except (TypeError, ValueError) as exc:
        raise ValueError('تاریخ وارد شده معتبر نیست') from exc


def gregorian_to_jalali(g_date):
    """Convert a Gregorian date or datetime to YYYY/MM/DD."""
    if isinstance(g_date, datetime.datetime):
        g_date = g_date.date()
    return jdatetime.date.fromgregorian(date=g_date).strftime('%Y/%m/%d')
