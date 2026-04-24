from project.qld.engine.utils.market.FX import fx_market
import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser

from ..base_trade import BaseTrade


class DiscountingFXForwardEngine:
    def __init__(self, fxSpot, domesticCurve, foreignCurve):
        self.fxSpot = fxSpot
        self.domesticCurve = domesticCurve
        self.foreignCurve = foreignCurve

    def calculate(self, fxForwardTrade):
        settleDate = fxForwardTrade.settlement_date_or_tenor

        spotDate = self.fxSpot.spotDate
        spotRate = self.fxSpot.spotRate
        spotRate0 = spotRate * self.domesticCurve.discount(spotDate) / self.foreignCurve.discount(spotDate)

        fxForwardRate = spotRate0 * self.foreignCurve.discount(settleDate) / self.domesticCurve.discount(settleDate)
        npv = self.domesticCurve.discount(settleDate) * fxForwardTrade.notional * (fxForwardRate - fxForwardTrade.strike)
        return npv


class FXForward(BaseTrade):
    __name__ = "FXForward"

    def __init__(self, evaluation_date, domestic_currency, notional_currency, foreign_currency, notional, calendar,
                 settlement_date_or_tenor, strike, domestic_discounting, foreign_discounting):
        super().__init__(evaluation_date)
        self.domestic_currency = domestic_currency
        self.foreign_currency = foreign_currency
        self.notional_currency = notional_currency
        self.notional = notional
        self.settlement_date_or_tenor = settlement_date_or_tenor
        self.calendar = calendar
        self.strike = strike
        self.domestic_discounting = domestic_discounting
        self.foreign_discounting = foreign_discounting

        self._parse_input()
        self._validate_input()

    def _validate_input(self):
        pass

    def _parse_input(self):
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.domestic_currency = self.domestic_currency.upper()
        self.foreign_currency = self.foreign_currency.upper()
        self.notional_currency = self.notional_currency.upper()
        self.notional = float(self.notional)
        self.settlement_date_or_tenor = dateParser.parse_date(self.settlement_date_or_tenor)
        self.calendar = tradeParser.parse_calendar(self.calendar)

    def setup(self, risk_conf=None):
        super().setup(risk_conf)

        # ql.Settings.instance().evaluationDate = self.evaluation_date
        # QLD.Settings.instance().evaluationDate = self.evaluation_date

    def _build_trade(self):
        return self

    def _build_engine(self):
        fxSpot = fx_market.getFXSpot(self.domestic_currency, self.foreign_currency, self.market_data, self.notional_currency)
        domesticCurve = self.market_data[self.domestic_discounting]
        foreignCurve = self.market_data[self.foreign_discounting]
        engine = DiscountingFXForwardEngine(fxSpot, domesticCurve, foreignCurve)
        return engine

    def setPricingEngine(self, pricingEngine):
        self.pricingEngine = pricingEngine

    def NPV(self):
        if self.pricingEngine is None:
            raise ValueError('No pricing engine set')
        return self.pricingEngine.calculate(self)

    def price(self, risk_conf=None):
        # setup market, input, and model config
        self.setup(risk_conf)

        # price trade
        trade = self._build_trade()
        engine = self._build_engine()
        trade.setPricingEngine(engine)

        self.result['npv'] = trade.NPV()
