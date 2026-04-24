from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql


class DiscountingFXForwardEngine:
    def __init__(self, fxSpot, domesticCurve, foreignCurve):
        self.fxSpot = fxSpot
        self.domesticCurve = domesticCurve
        self.foreignCurve = foreignCurve

    def calculate(self, fxForwardTrade):
        settleDate = fxForwardTrade.settlementDate

        spotDate = self.fxSpot.spotDate
        spotRate = self.fxSpot.spotRate
        spotRate0 = spotRate * self.domesticCurve.discount(spotDate) / self.foreignCurve.discount(spotDate)

        fxForwardRate = spotRate0 * self.foreignCurve.discount(settleDate) / self.domesticCurve.discount(settleDate)
        npv = self.domesticCurve.discount(settleDate) * fxForwardTrade.notional * (fxForwardRate - fxForwardTrade.strike)
        return npv

class BlachSholesFXVanillaOptionEngine:
    def __init__(self, fxSpot, domesticCurve, foreignCurve, fxVolSurface):
        self.fxSpot = fxSpot
        self.domesticCurve = domesticCurve
        self.foreignCurve = foreignCurve
        self.fxVolSurface = fxVolSurface

    def calculate(self, fxVanillaOptionTrade):
        expiryDate = fxVanillaOptionTrade.ExpiryDate
        settleDate = fxVanillaOptionTrade.SettlementDate

        spotDate = self.fxSpot.spotDate
        spotRate = self.fxSpot.spotRate
        spotRate0 = spotRate * self.domesticCurve.discount(spotDate) / self.foreignCurve.discount(spotDate)
        trade = fxVanillaOptionTrade.QlTrade
        notional = fxVanillaOptionTrade.Notional

        fxSpot0Quote = ql.QuoteHandle(ql.SimpleQuote(spotRate0))
        process = ql.BlackScholesMertonProcess(fxSpot0Quote, self.foreignCurve, self.domesticCurve, self.fxVolSurface[0])
        analyticEngine = ql.AnalyticEuropeanEngine(process, self.domesticCurve)
        trade.setPricingEngine(analyticEngine)
        undisc_price = notional * trade.NPV()

        disc = self.domesticCurve.discount(settleDate)
        npv = undisc_price * disc
        return npv

