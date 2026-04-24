from enum import Enum
\
from project.qld.engine.qld.QLD import ql
from project.qld.engine.utils.market.IR.ir_market import Sora


class SettlementCurrencyType(Enum):
    def __str__(self):
        return self.name
    NA = 0
    Domestic = 1
    Foreign = 2


def parse_calendar(calendars):
    if isinstance(calendars, str):
        calendarList = [s.upper().strip() for s in calendars.split("+")]
    elif isinstance(calendars, list):
        calendarList = [s.upper().strip() for s in calendars]
    else:
        raise ValueError(f'Calendar must be either a list or string ("+" as delimeter), found {type(calendars)}: {calendars}')
    cals = []
    for calStr in calendarList:
        if calStr == "LDN" or calStr == "UK":
            cals.append(ql.UnitedKingdom(ql.UnitedKingdom.Exchange))
        elif calStr == "NY" or calStr == "US":
            cals.append(ql.UnitedStates(ql.UnitedStates.NYSE))
        elif calStr == "SG":
            calSG = ql.Singapore()
            calSG.addHoliday(ql.Date(31, 10, 2024))
            cals.append(calSG)
        elif calStr == "TPE":
            cals.append(ql.Taiwan())
        elif calStr == "KL":
            cals.append(ql.Singapore())  # approximation
        elif calStr == "JKT":
            cals.append(ql.Indonesia())
        elif calStr == "TKY" or calStr == "JP":
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


def parse_dc(dcStr):
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


def parse_bdc(bdcStr):
    bdcStrUpper = bdcStr.upper()
    if bdcStrUpper == "MODIFIEDFOLLOWING":
        return ql.ModifiedFollowing
    elif bdcStrUpper == "FOLLOWING":
        return ql.Following
    elif bdcStrUpper == "PRECEDING":
        return ql.Preceding
    else:
        raise ValueError("Unknown business day convention: " + bdcStr)


def parse_ccy(ccyText):
    if isinstance(ccyText, ql.Currency):
        return ccyText

    ccyText = ccyText.upper()
    if ccyText == "USD":
        return ql.USDCurrency()
    elif ccyText == "EUR":
        return ql.EURCurrency()
    elif ccyText == "JPY":
        return ql.JPYCurrency()
    elif ccyText == "GBP":
        return ql.GBPCurrency()
    elif ccyText == "MYR":
        return ql.MYRCurrency()
    elif ccyText == "SGD":
        return ql.SGDCurrency()
    elif ccyText == "IDR":
        return ql.IDRCurrency()
    else:
        raise ValueError("Unknown currency symbol: " + ccyText)


def parse_IROisIndex(currency, forecastCurve=None):
    if currency == ql.USDCurrency():
        if forecastCurve == None:
            return ql.Sofr()
        else:
            return ql.Sofr(forecastCurve)
    elif currency == ql.GBPCurrency():
        if forecastCurve == None:
            return ql.Sonia()
        else:
            return ql.Sonia(forecastCurve)
    elif currency == ql.SGDCurrency():
        if forecastCurve == None:
            return Sora()
        else:
            return Sora(forecastCurve)
    else:
        raise ("Unkown OIS SWAP for currency:" + currency.code())


def parse_IRIborIndex(index, forecastCurve=None):
    ''' index of format "USD.LIBOR.3M" '''
    def KualaLumpur():
        return ql.Singapore()

    currency, _, tenor = index.split(".")
    currency = parse_ccy(currency)
    tenor = ql.Period(tenor) if tenor is not None else ql.Period("3M")

    if currency == ql.USDCurrency():
        if forecastCurve is None:
            return ql.USDLibor(tenor)
        else:
            return ql.USDLibor(tenor, forecastCurve)
    elif currency == ql.MYRCurrency():
        if forecastCurve is None:
            return ql.Libor("KLibor", tenor, 0, ql.MYRCurrency(),
                            KualaLumpur(),
                            ql.Actual365Fixed())
        else:
            return ql.Libor("KLibor", tenor, 0, ql.MYRCurrency(),
                            KualaLumpur(),
                            ql.Actual365Fixed(), forecastCurve)


def get_currency_pair(ccy1, ccy2):
    """Generate currency pair according to ISO FX conventions."""
    # Major currencies in order of precedence
    major_order = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']

    ccy1, ccy2 = ccy1.upper(), ccy2.upper()

    if ccy1 == ccy2:
        raise ValueError("Cannot create pair with same currency")

    # Check if both are major currencies
    if ccy1 in major_order and ccy2 in major_order:
        # Use the one with higher precedence as base
        if major_order.index(ccy1) < major_order.index(ccy2):
            return f"{ccy1}{ccy2}"
        else:
            return f"{ccy2}{ccy1}"

    # If only one is major, it becomes base (except USD)
    if ccy1 in major_order and ccy2 not in major_order:
        if ccy1 == 'USD':
            return f"USD{ccy2}"
        else:
            return f"{ccy1}USD" if ccy2 == 'USD' else f"{ccy1}{ccy2}"

    if ccy2 in major_order and ccy1 not in major_order:
        if ccy2 == 'USD':
            return f"USD{ccy1}"
        else:
            return f"{ccy2}USD" if ccy1 == 'USD' else f"{ccy2}{ccy1}"

    # Both are minor currencies - alphabetical order
    return f"{ccy1}{ccy2}" if ccy1 < ccy2 else f"{ccy2}{ccy1}"


def parse_settlement_type(settlementTypeStr):
    typeUpper = settlementTypeStr.upper()
    if typeUpper == "PHYSICAL":
        return ql.Settlement.Physical, SettlementCurrencyType.NA
    elif typeUpper == "CASHDOMESTIC":
        return ql.Settlement.Cash, SettlementCurrencyType.Domestic
    elif typeUpper == "CASHFOREIGN":
        return ql.Settlement.Cash, SettlementCurrencyType.Foreign
    else:
        raise ValueError("Unknown settlement type: " + settlementTypeStr)
