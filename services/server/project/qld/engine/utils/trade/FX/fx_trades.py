from enum import Enum
from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql
from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.market import parseUtils


class FXForward:
    def __init__(self, domCcy, forCcy, nomCcy, notional, calendar, settlementDate, timeCut, strike, domCurveName, forCurveName):
        self.domCcy = domCcy.upper()
        self.forCcy = forCcy.upper()
        self.nomCcy = nomCcy.upper()
        self.notional = notional
        # self.calendar = calendar
        self.settlementDate = settlementDate
        # self.timeCut = timeCut
        self.strike = strike
        # self.domCurveName = domCurveName
        # self.forCurveName = forCurveName

    pricingEngine = None

    def setPricingEngine(self, pricingEngine):
        self.pricingEngine = pricingEngine

    def NPV(self):
        return self.pricingEngine.calculate(self)


def parseFXForward(dfTrade):
    calendar = parseUtils.parseCalendar(dfTrade.Calendar)
    settlementTenor = dfTrade.SettlementDateOrTenor
    if isinstance(settlementTenor, str):
        settlementTenor = ql.Period(settlementTenor)
        evaluationDate = ql.Settings.instance().evaluationDate
        settlementDate = calendar.advance(evaluationDate, settlementTenor)
    else:
        settlementDate = du.pythonDateTime2QLDDate(settlementTenor)
    return FXForward(dfTrade.DomesticCurrency, dfTrade.ForeignCurrency, dfTrade.NotionalCurrency, dfTrade.Notional, calendar,
                     settlementDate, dfTrade.TimeCut, dfTrade.Strike, dfTrade.DomesticDiscounting, dfTrade.ForeignDiscounting)

# just a special version of FX forward, where the settlement date is start date + 2
# physical delivery, so no fixing date


def parseFXSpot(dfTrade):
    return parseFXForward(dfTrade)


class SettlementCurrencyType(Enum):
    def __str__(self):
        return self.name
    NA = 0
    Domestic = 1
    Foreign = 2


class FXVanillaOption:
    def __init__(self, domCcy, forCcy, nomCcy, notional, calendar, expiryDateOrTenor, settlementTenor, timeCut, strike, optionType, domCurveName, forCurveName, fxVolSurfaceName):
        self.domCcy = domCcy.upper()
        self.forCcy = forCcy.upper()
        self.nomCcy = nomCcy.upper()
        self.notional = notional
        # self.calendar = calendar
        self.expiryDateOrTenor = expiryDateOrTenor
        self.settlementTenor = settlementTenor
        # self.timeCut = timeCut
        self.strike = strike
        self.optionType = optionType
        # self.domCurveName = domCurveName
        # self.forCurveName = forCurveName

        evaluationDate = ql.Settings.instance().evaluationDate
        calendar = parseUtils.parseCalendar(calendar)
        if isinstance(expiryDateOrTenor, str):
            expiryTenor = ql.Period(expiryDateOrTenor)
            expiryDate = calendar.advance(evaluationDate, expiryTenor)
        else:
            expiryDate = du.pythonDateTime2QLDDate(expiryDateOrTenor)

        if isinstance(settlementTenor, str):
            settlementTenor = ql.Period(settlementTenor)
            settlementDate = calendar.advance(expiryDate, settlementTenor)
        else:
            settlementDate = du.pythonDateTime2QLDDate(settlementTenor)

        # ususally, notional currency = foreign currency: N * Max(S - K, 0)
        # but, if notionary currency is domectic currency:
        # 1. Flip call/put
        # 2. N(domestic) --> N / K
        if nomCcy == forCcy:
            optionType = QLD.Option.Call if optionType.upper() == "CALL" else QLD.Option.Put
        else:
            optionType = QLD.Option.Put if optionType.upper() == "CALL" else QLD.Option.Call
            notional = notional / strike

        payoff = ql.PlainVanillaPayoff(optionType, float(strike))
        europeanExercise = ql.EuropeanExercise(expiryDate)
        vanillaOption = ql.VanillaOption(payoff, europeanExercise)
        self.ExpiryDate = expiryDate
        self.SettlementDate = settlementDate
        self.Notional = notional
        self.QlTrade = vanillaOption

    pricingEngine = None

    def setPricingEngine(self, pricingEngine):
        self.pricingEngine = pricingEngine

    def NPV(self):
        return self.pricingEngine.calculate(self)


def parseFXVanillaOption(dfTrade):
    return FXVanillaOption(dfTrade.DomesticCurrency, dfTrade.ForeignCurrency, dfTrade.NotionalCurrency,
                           dfTrade.Notional, dfTrade.Calendar,
                           dfTrade.ExpiryDateOrTenor, dfTrade.SettlementTenor, "", dfTrade.Strike,
                           dfTrade.OptionType, dfTrade.DomesticDiscounting, dfTrade.ForeignDiscounting,
                           dfTrade.FXVolSurface
                           )
    # return {"SettlementDate": settlementDate,
    #         "Notional": dfTrade.Notional,
    #         "Trade": vanillaOption}


def parseSettlementType(settlementTypeStr):
    typeUpper = settlementTypeStr.upper()
    if typeUpper == "PHYSICAL":
        return ql.Settlement.Physical, SettlementCurrencyType.NA
    elif typeUpper == "CASHDOMESTIC":
        return ql.Settlement.Cash, SettlementCurrencyType.Domestic
    elif typeUpper == "CASHFOREIGN":
        return ql.Settlement.Cash, SettlementCurrencyType.Foreign
    else:
        raise ValueError("Unknown settlement type: " + settlementTypeStr)
