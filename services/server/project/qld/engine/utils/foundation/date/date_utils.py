from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql
import datetime as dt
# from datetime import datetime as dt


def pythonDateTime2ExcelSerial(pythonDatetime):
    offset = 693594
    itime = dt.date(pythonDatetime.year, pythonDatetime.month, pythonDatetime.day)
    n = itime.toordinal()
    floatRet = (n - offset + (60.*60.*pythonDatetime.hour + 60.*pythonDatetime.minute + pythonDatetime.second) / (24.*60.*60.))
    return int(floatRet)


def pythonDateTime2QLDDate(pythonDatetime):
    return ql.Date(pythonDatetime.day, pythonDatetime.month, pythonDatetime.year)


def simpleYearFraction(period):
    n = period.length()
    unit = period.units()
    if unit == ql.Years:
        ratio = 1.0
    elif unit == ql.Months:
        ratio = 1./12.
    elif unit == ql.Weeks:
        ratio = 7./365.
    elif unit == ql.Days:
        ratio = 1./365.
    else:
        raise Exception("unknown date unit: " + str(unit))
    return float(n)*ratio


def monthsFromPeriod(period):
    n = period.length()
    unit = period.units()
    if unit == ql.Years:
        ratio = 12.
    elif unit == ql.Months:
        ratio = 1.
    elif unit == ql.Weeks:
        ratio = 12.*7./365.
    elif unit == ql.Days:
        ratio = 12./365.
    else:
        raise Exception("unknown date unit: " + str(unit))
    return float(n)*ratio


def dateYYYYMMDD(date):
    if isinstance(date, dt.datetime):
        return str(date.year).zfill(4) + str(date.month).zfill(2) + str(date.day).zfill(2)
    elif isinstance(date, ql.Date):
        return str(date.year()).zfill(4) + str(date.month()).zfill(2) + str(date.dayOfMonth()).zfill(2)
    else:
        raise ValueError("unknown date type: " + str(date))
