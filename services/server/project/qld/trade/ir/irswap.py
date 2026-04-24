from project.qld.engine.qld.QLD import ql
import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser

from ..base_trade import BaseTrade


class IRSwap(BaseTrade):
    __name__ = "IRSwap"

    def __init__(self, evaluation_date, currency, notional, start_date, end_date, calendar,
                 fixing_lag, business_day_convention, type,
                 fixed_rate, fixed_frequency, fixed_day_count,
                 float_index, float_spread, float_frequency, float_day_count,
                 discounting_curve):
        super().__init__(evaluation_date)
        self.currency = currency
        self.notional = notional
        self.start_date = start_date
        self.end_date = end_date
        self.calendar = calendar
        self.fixing_lag = fixing_lag
        self.business_day_convention = business_day_convention
        self.type = type
        self.fixed_rate = fixed_rate
        self.fixed_frequency = fixed_frequency
        self.fixed_day_count = fixed_day_count
        self.float_index = float_index
        self.float_spread = float_spread
        self.float_frequency = float_frequency
        self.float_day_count = float_day_count
        self.discounting_curve = discounting_curve

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.currency = tradeParser.parse_ccy(self.currency)
        self.notional = float(self.notional)
        self.start_date = dateParser.parse_date(self.start_date)
        self.end_date = dateParser.parse_date(self.end_date)
        self.calendar = tradeParser.parse_calendar(self.calendar)
        self.fixing_lag = int(self.fixing_lag)
        self.business_day_convention = tradeParser.parse_bdc(self.business_day_convention)
        self.fixed_rate = float(self.fixed_rate)
        self.fixed_frequency = ql.Period(self.fixed_frequency)
        self.fixed_day_count = tradeParser.parse_dc(self.fixed_day_count)
        self.float_frequency = ql.Period(self.float_frequency)
        self.float_spread = float(self.float_spread)
        self.float_day_count = tradeParser.parse_dc(self.float_day_count)

    def _validate_input(self):
        pass

    def _build_trade(self):
        ccy = self.currency
        forecast_curve = self.market_data[self.float_index]
        index = tradeParser.parse_IRIborIndex(self.float_index, forecast_curve)

        if ccy == ql.USDCurrency():  # temporary code for fixing
            # Source is Bloomberg otherwise stated
            # Market watch https://www.marketwatch.com/investing/interestrate/liborusd3m?countrycode=mr
            index.addFixing(ql.Date(31, 3, 2022), 0.96157 / 100.0)

        fixed_schedule = ql.Schedule(self.start_date, self.end_date, self.fixed_frequency, self.calendar,
                                     self.business_day_convention, self.business_day_convention, ql.DateGeneration.Forward, False)
        float_schedule = ql.Schedule(self.start_date, self.end_date, self.float_frequency, self.calendar,
                                     self.business_day_convention, self.business_day_convention, ql.DateGeneration.Forward, False)

        if self.type.upper() == "PAYER":
            swapType = ql.VanillaSwap.Payer
        elif self.type.upper() == "RECEIVER":
            swapType = ql.VanillaSwap.Receiver
        else:
            raise ValueError("Unknown vanilla swap type: " + self.type)
        return ql.VanillaSwap(swapType, self.notional, fixed_schedule, self.fixed_rate, self.fixed_day_count, float_schedule, index, self.float_spread, self.float_day_count)

    def price(self, risk_conf=None):
        # setup market, input, and model config
        self.setup(risk_conf)

        # price trade
        trade = self._build_trade()
        discountCurve = self.market_data[self.discounting_curve]
        engine = ql.DiscountingSwapEngine(discountCurve)
        trade.setPricingEngine(engine)
        self.result['npv'] = trade.NPV()
