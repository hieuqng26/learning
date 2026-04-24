import pandas as pd
from project.qld.engine.qld.QLD import ql
import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser

from ..base_trade import BaseTrade, MARKET_DATA_PATH


class OISwap(BaseTrade):
    __name__ = "OISwap"

    def __init__(self, evaluation_date, currency, notional, start_date, end_date, calendar,
                 payment_lag, business_day_convention, type,
                 fixed_rate, fixed_frequency, fixed_day_count,
                 overnight_index, overnight_spread, overnight_day_count,
                 discounting_curve):
        super().__init__(evaluation_date)
        self.currency = currency
        self.notional = notional
        self.start_date = start_date
        self.end_date = end_date
        self.calendar = calendar
        self.payment_lag = payment_lag
        self.business_day_convention = business_day_convention
        self.type = type
        self.fixed_rate = fixed_rate
        self.fixed_frequency = fixed_frequency
        self.fixed_day_count = fixed_day_count
        self.overnight_index = overnight_index
        self.overnight_spread = overnight_spread
        self.overnight_day_count = overnight_day_count
        self.discounting_curve = discounting_curve

        self._parse_input()
        self._validate_input()

    def _add_fixing(self):
        ccy = self.currency
        forecast_curve = self.market_data[self.overnight_index]
        index = tradeParser.parse_IROisIndex(ccy, forecast_curve)

        if ccy == ql.USDCurrency():
            file_path = MARKET_DATA_PATH / 'YIELDCURVE/Historical_SOFR_Data.xlsx'
        elif ccy == ql.SGDCurrency():
            file_path = MARKET_DATA_PATH / 'YIELDCURVE/Historical_SORA_Data.xlsx'
        elif ccy == ql.GBPCurrency():
            file_path = MARKET_DATA_PATH / 'YIELDCURVE/Historical_SONIA_Data.xlsx'
        else:
            raise ValueError("Unknown currency: " + ccy.code())

        df = pd.read_excel(file_path)
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])
        for _, row in df.iterrows():
            date = ql.Date(row['Effective Date'].day, row['Effective Date'].month, row['Effective Date'].year)
            rate = row['Rate']
            index.addFixing(date, rate)
        self.index = index

    def _validate_input(self):
        pass

    def _parse_input(self):
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.currency = tradeParser.parse_ccy(self.currency)
        self.notional = float(self.notional)
        self.start_date = dateParser.parse_date(self.start_date)
        self.end_date = dateParser.parse_date(self.end_date)
        self.calendar = tradeParser.parse_calendar(self.calendar)
        self.payment_lag = int(self.payment_lag)
        self.business_day_convention = tradeParser.parse_bdc(self.business_day_convention)
        self.fixed_rate = float(self.fixed_rate)
        self.fixed_frequency = ql.Period(self.fixed_frequency)
        self.fixed_day_count = tradeParser.parse_dc(self.fixed_day_count)
        self.overnight_day_count = tradeParser.parse_dc(self.overnight_day_count)

    def setup(self, risk_conf=None):
        super().setup(risk_conf)
        self._add_fixing()

        # ql.Settings.instance().evaluationDate = self.evaluation_date
        # QLD.Settings.instance().evaluationDate = self.evaluation_date

    def _build_trade(self):
        schedule = ql.Schedule(self.start_date, self.end_date, self.fixed_frequency, self.calendar,
                               self.business_day_convention, self.business_day_convention,
                               ql.DateGeneration.Forward, False)
        if self.type.upper() == 'PAYER':
            swapType = ql.OvernightIndexedSwap.Payer
        elif self.type.upper() == 'RECEIVER':
            swapType = ql.OvernightIndexedSwap.Receiver
        else:
            raise ValueError("Unknown ois swap type: " + self.type)

        return ql.OvernightIndexedSwap(swapType, self.notional, schedule, self.fixed_rate,
                                       self.fixed_day_count, self.index, self.overnight_spread,
                                       int(self.payment_lag))

    def price(self, risk_conf=None):
        # setup market, input, and model config
        self.setup(risk_conf)

        # price trade
        trade = self._build_trade()
        discountCurve = self.market_data[self.discounting_curve]
        engine = ql.DiscountingSwapEngine(discountCurve)
        trade.setPricingEngine(engine)
        self.result['npv'] = trade.NPV()
