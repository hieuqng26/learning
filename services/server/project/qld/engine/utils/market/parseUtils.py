from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.qld.QLD import ql

from project.qld.engine.utils.pricing import riskConfiguration as riskconf


def parseCalendar(calendars):
    if isinstance(calendars, str):
        calendarList = [s.upper().strip() for s in calendars.split("+")]
    elif isinstance(calendars, list):
        calendarList = [s.upper().strip() for s in calendars]
    else:
        raise ValueError(f'Calendar must be either a list or string ("+" as delimeter), found {type(calendars)}: {calendars}')
    cals = []
    for calStr in calendarList:
        if calStr == "LDN":
            cals.append(ql.UnitedKingdom(ql.UnitedKingdom.Exchange))
        elif calStr == "NY":
            cals.append(ql.UnitedStates(ql.UnitedStates.NYSE))
        elif calStr == "SG":
            calSG = ql.Singapore()
            calSG.addHoliday(ql.Date(31, 10, 2024))
            cals.append(calSG)
            # cals.append(ql.Singapore())
        elif calStr == "TPE":
            cals.append(ql.Taiwan())
        elif calStr == "KL":
            cals.append(KualaLumpur())
        elif calStr == "JKT":
            cals.append(ql.Indonesia())
        elif calStr == "TKY":
            cals.append(ql.Japan())
        elif calStr == "TARGET" or calStr == "EUR":
            cals.append(ql.TARGET())
        elif calStr == "IST":
            cals.append(ql.Turkey())
        elif calStr == "SH" or calStr == "BJ":
            cals.append(ql.China())
        elif calStr == "MUM":
            cals.append(ql.India())
        elif calStr == "BKK":
            cals.append(ql.Thailand())
        elif calStr == "HK":
            cals.append(ql.HongKong())
        elif calStr == 'SYD':
            cals.append(ql.Australia())
        elif calStr == 'POL':
            cals.append(ql.Poland())
        elif calStr == 'SWE':
            cals.append(ql.Sweden())
        elif calStr == 'NOR':
            cals.append(ql.Norway())
        elif calStr == 'SAR':
            cals.append(ql.SouthAfrica())
        else:
            raise Exception("Unknown calendar " + calStr)
    if cals is None:
        cal = None
    elif len(cals) == 1:
        cal = cals[0]
    elif len(cals) < 5:
        cal = ql.JointCalendar(*cals)
    else:
        cal = ql.JointCalendar(*(cals[0:3]))
        for i in range(4, len(cals)):
            cal = ql.JointCalendar(cal, cals[i])
    return cal


def parseRiskConfiguration(riskConf, targetMarketObjectName):
    bumpObjectsOnTarget = []
    dateShifts = []
    bumpSizes = []
    if riskConf is not None and riskConf.bumpObjects is not None:  # and riskConf.riskType != riskconf.RiskType.NPV
        for bumpObject in riskConf.bumpObjects:
            bumpObjectOnTarget = None
            dateShift = None
            bumpSize = None
            if riskConf.riskType == riskconf.RiskType.Theta:
                dateShift = bumpObject.bumpSize
                bumpObjectOnTarget = bumpObject
            else:
                for bumpObject in riskConf.bumpObjects:
                    if bumpObject.bumpObjectName == targetMarketObjectName:
                        bumpSize = (bumpSize + bumpObject.bumpSize) if bumpSize else 0.0
                        bumpObjectOnTarget = bumpObject

            bumpObjectsOnTarget.append(bumpObjectOnTarget)
            dateShifts.append(dateShift)
            bumpSizes.append(bumpSize)
    return bumpObjectsOnTarget, dateShifts, bumpSizes


def bumpDate(date, dateShiftString, calendar):
    if not dateShiftString:
        return date
    length = int(''.join(filter(str.isdigit, dateShiftString)))
    unit = dateShiftString[(len(str(length))):].upper()
    if length == 0:
        bumpedDate = date
    elif unit == "BD":
        dateShift = ql.Period(length, ql.Days)
        bumpedDate = calendar.advance(date, dateShift)
    elif unit == "CD" or unit == "D":
        bumpedDate = date + length
    else:
        raise Exception("Unknown day unit: " + unit)
    return bumpedDate


def bumpDateMultiple(date, dateShiftsString, calendar):
    bumpedDate = date
    for dateShiftString in dateShiftsString:
        bumpedDate = bumpDate(bumpedDate, dateShiftString, calendar)
    return bumpedDate


def parseEvaluationDate(dfs, riskConf):
    headerTable = dfs[0]
    originalEvaluationDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "Date"]["Value"].values[0])

    bumpObjects, dateShifts, bumpSizes = parseRiskConfiguration(riskConf, "")

    calendarStr = headerTable.loc[headerTable["Key"] == "Calendar"]["Value"].values[0]
    calendar = parseCalendar(calendarStr)

    evaluationDate = bumpDateMultiple(originalEvaluationDate, dateShifts, calendar)
    return evaluationDate


def KualaLumpur():
    return ql.Singapore()  # approximation


def parseDayCount(dcStr):
    dcStrUpper = str(dcStr).upper().strip()
    if dcStrUpper == "ACTUAL360" or dcStrUpper == "ACTUAL/360" or dcStrUpper == "ACT360" or dcStrUpper == "ACT/360":
        return ql.Actual360()
    if dcStrUpper == "ACTUAL365FIXED" or dcStrUpper == "ACTUAL/365FIXED" or dcStrUpper == "ACT365F":
        return ql.Actual365Fixed()
    elif dcStrUpper == "30360" or dcStrUpper == "30/360" or dcStrUpper == "THIRTY360":
        return ql.Thirty360(ql.Thirty360.BondBasis)
    elif dcStrUpper == "ACT/ACT" or dcStrUpper == "ACTUAL/ACTUAL" or dcStrUpper == "ACT/ACT(ICMA)" or dcStrUpper == "ACT/ACT(ISMA)":
        # ACT/ACT(ICMA) and (ISMA) are identical
        # https://www.isda.org/2011/01/07/act-act-icma/
        return ql.ActualActual(ql.ActualActual.ISMA)
    else:
        raise ValueError("Unkown day counter: " + dcStr)


def parseBusinessDayConvention(bdcStr):
    bdcStrUpper = bdcStr.upper()
    if bdcStrUpper == "MODIFIEDFOLLOWING":
        return ql.ModifiedFollowing
    elif bdcStrUpper == "FOLLOWING":
        return ql.Following
    elif bdcStrUpper == "PRECEDING":
        return ql.Preceding
    else:
        raise ValueError("Unknown business day convention: " + bdcStr)
