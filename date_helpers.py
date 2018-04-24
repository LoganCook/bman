import calendar
import datetime

import pytz

DAY_IN_SECS = 86399  # 24 * 60 * 60 - 1


def date_string_to_timestamp(date_string, tz='Australia/Adelaide', fmt='%Y%m%d'):
    """Parse a date string of a given timezone and return timestamp of it
    at the begining of the day:

    20170101 (Sunday 1 January  00:00:00 ACDT 2017) -> 1483191000

    date_string: string, e.g. 20170101 or 2017-01-01
    tz: string, official time zone string, default is Australia/Adelaide
    fmt: string, the format of date_string, default is %Y%m%d
    return int timestamp
    """
    target_tz = pytz.timezone(tz)
    local_date = datetime.datetime.strptime(date_string, fmt)
    target_date = target_tz.localize(local_date)
    return int(target_date.timestamp())


def date_range_to_timestamps(start, end, tz='Australia/Adelaide', fmt='%Y%m%d'):
    """Convert start and end dates to timestamps"""
    try:
        min_date = date_string_to_timestamp(start, tz, fmt)
    except Exception as e:
        raise ValueError("Not a valid date string: %s" % str(e))

    try:
        max_date = date_string_to_timestamp(end, tz, fmt) + DAY_IN_SECS
    except Exception as e:
        raise ValueError("Not a valid date string: %s" % str(e))
    return min_date, max_date


def day_to_timestamps(date_string, tz='Australia/Adelaide', fmt='%Y%m%d'):
    """Convert a date to the start and end timestamps"""
    try:
        min_date = date_string_to_timestamp(date_string, tz, fmt)
    except Exception as e:
        raise ValueError("Not a valid date string: %s" % str(e))

    return min_date, min_date + DAY_IN_SECS


def year_to_timestamp(year, tz='Australia/Adelaide'):
    """Convert a year to the timestamp of the first second of the year"""
    return date_string_to_timestamp('%d0101' % int(year), tz)


def month_to_timestamp(year, month, tz='Australia/Adelaide'):
    """Convert a month of a year to the timestamp of the first second of the month"""
    return date_string_to_timestamp('%d%0.2d01' % (int(year), int(month)), tz)


def month_to_start_end_date_strings(year, month):
    """Get date strings in the format of %Y%m%d for start and end of a month of a year"""
    def _last_day(year, month):
        """Get the last day in the year and the month"""
        assert month > 0 and month < 13, 'Month must be in 1..12'
        return calendar.monthrange(year, month)[1]

    if isinstance(year, str):
        year = int(year)
    if isinstance(month, str):
        month = int(month)
    return '%d%d%d' % (year, month, 1), \
           '%d%d%d' % (year, month, _last_day(year, month))


def month_to_start_end_timestamps(year, month):
    """Get timestamps for start and end of a month of a year"""
    return date_range_to_timestamps(*month_to_start_end_date_strings(year, month))
