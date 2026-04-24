from project.qld.engine.qld.QLD import ql
from project.qld.engine.qld import QLD

from project.qld.engine.utils.market.FX import fx_market

import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser

from ..base_trade import BaseTrade


class FXVanillaOption(BaseTrade):
    __name__ = "FXVanillaOption"

    def __init__(self, evaluation_date, domestic_currency, notional_currency, foreign_currency, notional, expiry_date, calendar,
                 settlement_tenor, option_type, strike, settlement_type, domestic_discounting, foreign_discounting, fx_vol_surface):
        super().__init__(evaluation_date)
        self.domestic_currency = domestic_currency
        self.foreign_currency = foreign_currency
        self.notional_currency = notional_currency
        self.notional = notional
        self.expiry_date = expiry_date
        self.settlement_tenor = settlement_tenor
        self.option_type = option_type
        self.calendar = calendar
        self.strike = strike
        self.settlement_type = settlement_type
        self.domestic_discounting = domestic_discounting
        self.foreign_discounting = foreign_discounting
        self.fx_vol_surface = fx_vol_surface

        self._parse_input()
        self._validate_input()

    def _load_market_data(self, risk_conf=None):
        super()._load_market_data(risk_conf)

        self.domestic_discounting_ = self.market_data[self.domestic_discounting]
        self.foreign_discounting_ = self.market_data[self.foreign_discounting]
        self.fx_vol_surface_ = self.market_data[self.fx_vol_surface]

    def _validate_input(self):
        pass

    def _parse_input(self):
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.domestic_currency = self.domestic_currency.upper()
        self.foreign_currency = self.foreign_currency.upper()
        self.notional_currency = self.notional_currency.upper()
        self.notional = float(self.notional)
        self.strike = float(self.strike)
        self.expiry_date = dateParser.parse_date(self.expiry_date)
        self.settlement_tenor = ql.Period(self.settlement_tenor)
        self.settlement_type = tradeParser.parse_settlement_type(self.settlement_type)
        self.calendar = tradeParser.parse_calendar(self.calendar)

        if self.notional_currency == self.foreign_currency:
            self.option_type = QLD.Option.Call if self.option_type.upper() == "CALL" else QLD.Option.Put
        else:
            self.option_type = QLD.Option.Put if self.option_type.upper() == "CALL" else QLD.Option.Call
            self.notional = self.notional / self.strike

        self.settlement_date = self.calendar.advance(self.expiry_date, self.settlement_tenor)

    def setup(self, risk_conf=None):
        super().setup(risk_conf)

        # ql.Settings.instance().evaluationDate = self.evaluation_date
        # QLD.Settings.instance().evaluationDate = self.evaluation_date

    def _build_trade(self):
        payoff = ql.PlainVanillaPayoff(self.option_type, self.strike)
        europeanExercise = ql.EuropeanExercise(self.expiry_date)
        trade = ql.VanillaOption(payoff, europeanExercise)
        return trade

    def _build_engine(self):
        fxSpot = fx_market.getFXSpot(self.domestic_currency, self.foreign_currency, self.market_data, self.notional_currency)

        spotDate = fxSpot.spotDate
        spotRate = fxSpot.spotRate

        spotRate0 = spotRate * self.domestic_discounting_.discount(spotDate) / self.foreign_discounting_.discount(spotDate)
        fxSpot0Quote = ql.QuoteHandle(ql.SimpleQuote(spotRate0))
        process = ql.BlackScholesMertonProcess(fxSpot0Quote, self.foreign_discounting_, self.domestic_discounting_, self.fx_vol_surface_[0])
        engine = ql.AnalyticEuropeanEngine(process, self.domestic_discounting_)

        return engine

    def price(self, risk_conf=None):
        # setup market, input, and model config
        self.setup(risk_conf)

        # price trade
        trade = self._build_trade()
        engine = self._build_engine()
        trade.setPricingEngine(engine)

        undisc_price = self.notional * trade.NPV()
        disc = self.domestic_discounting_.discount(self.settlement_date)
        npv = undisc_price * disc

        self.result['npv'] = npv
