from project.qld.engine.qld.QLD import ql
import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser

from ..base_trade import BaseTrade


class IRFixedRateBond(BaseTrade):
    __name__ = "IRFixedRateBond"

    def __init__(self, evaluation_date, currency, notional, start_date, end_date, calendar,
                 day_count_convention, business_day_convention, settlement_lag, fixed_rate,
                 fixed_frequency, discounting_curve):
        super().__init__(evaluation_date)
        self.currency = currency
        self.notional = notional
        self.start_date = start_date
        self.end_date = end_date
        self.calendar = calendar
        self.day_count_convention = day_count_convention
        self.business_day_convention = business_day_convention
        self.settlement_lag = settlement_lag
        self.fixed_rate = fixed_rate
        self.fixed_frequency = fixed_frequency
        self.discounting_curve = discounting_curve

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        self.settlement_lag = int(self.settlement_lag)
        self.calendar = tradeParser.parse_calendar(self.calendar)
        self.start_date = dateParser.parse_date(self.start_date)
        self.end_date = dateParser.parse_date(self.end_date)
        self.notional = float(self.notional)
        self.fixed_frequency = ql.Period(self.fixed_frequency)
        self.fixed_rate = float(self.fixed_rate)
        self.day_count_convention = tradeParser.parse_dc(self.day_count_convention)
        self.business_day_convention = tradeParser.parse_bdc(self.business_day_convention)

    def _validate_input(self):
        pass

    def _build_trade(self):
        trade = ql.FixedRateBond(
            self.settlement_lag,
            self.calendar,
            self.notional,
            self.start_date,
            self.end_date,
            self.fixed_frequency,
            [self.fixed_rate],
            self.day_count_convention,
            self.business_day_convention
        )
        return trade

    def price(self, risk_conf=None):
        self.setup(risk_conf)

        # evaluationDate = dateParser.parse_date(self.evaluation_date)
        # ql.Settings.instance().evaluationDate = evaluationDate
        # QLD.Settings.instance().evaluationDate = evaluationDate

        trade = self._build_trade()
        discountCurve = self.market_data[self.discounting_curve]
        engine = ql.DiscountingBondEngine(discountCurve)
        trade.setPricingEngine(engine)
        self.result['npv'] = trade.NPV()
