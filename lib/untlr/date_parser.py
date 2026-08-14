"""
Utilities to convert timestamp (UNIX time) to Tumblr variables
"""
from typing import Any
from datetime import datetime, UTC

def _getMonthSuffix(day):
    """get date suffix such as 1st, 2nd, 3rd, 4th, ..."""
    if day == 1:
        return "st"
    if day == 2:
        return "nd"
    if day == 3:
        return "rd"
    return "th"

DATE_FORMAT = {
    "DayOfMonth": lambda x:x.day,
    "DayOfMonthWithZero": "%d",
    "DayOfWeek": "%A",
    "ShortDayOfWeek": "%a",
    "DayOfWeekNumber": "%w",
    "DayOfMonthSuffix": _getMonthSuffix,
    "DayOfYear": "%j",
    "WeekOfYear": "%U",
    "Month": "%B",
    "ShortMonth": "%b",
    "MonthNumber": lambda x:x.month,
    "MonthNumberWithZero": "%m",
    "Year": "%Y",
    "ShortYear": "%y",
    "AmPm": "%p",
    "CapitalAmPm": lambda x:"PM" if (x.day > 12) else "AM",
    "12Hour": lambda x:x.hour if (x.hour < 13) else (x.hour - 12),
    "24Hour": lambda x:x.hour,
    "12HourWithZero": "%I",
    "24HourWithZero": "%H",
    "Minutes": lambda x:x.minute,
    "Seconds": lambda x:x.second,
    #"Beats": "",
    #"Timestamp": "",
    #"TimeAgo": "",
}

def parse_timestamp(timestamp: int) -> dict[str, Any]:
    result = {}
    dt = datetime.fromtimestamp(timestamp, UTC)
    for k, v in DATE_FORMAT.items():
        if isinstance(v, str):
            result[k] = dt.strftime(v)
            continue
        if callable(v):
            result[k] = v(dt)
    result["Timestamp"] = timestamp
    result["TimeAgo"] = "xx ago(unimplemented)"
    return result
