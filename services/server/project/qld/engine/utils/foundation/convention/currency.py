from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql


def getCurrency(ccyText):
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
    else:
        raise ValueError("Unknown currency symbol: " + ccyText)
