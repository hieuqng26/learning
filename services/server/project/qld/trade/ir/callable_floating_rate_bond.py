import pandas as pd

import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser
from project.qld.engine.qld.QLD import ql
from project.qld.engine.qld import QLD

from ..base_trade import BaseTrade, MARKET_DATA_PATH


class CallableFloatingRateBond(BaseTrade):
    __name__ = "CallableFloatingRateBond"

    def __init__(self, evaluation_date, currency, notional, start_date, bond_tenor,
                 calendar, day_count_convention, business_day_convention,
                 option_tenors, exercise_lag, discount_curve_name, forecast_curve_name, vol_matrix,
                 spread, gearing=1.0):
        super().__init__(evaluation_date)
        self.currency = currency
        self.notional = notional
        self.start_date = start_date
        self.bond_tenor = bond_tenor
        self.calendar = calendar
        self.day_count_convention = day_count_convention
        self.business_day_convention = business_day_convention
        self.option_tenors = option_tenors
        self.exercise_lag = exercise_lag
        self.discount_curve_name = discount_curve_name
        self.forecast_curve_name = forecast_curve_name
        self.vol_matrix = vol_matrix
        self.spread = spread
        self.gearing = gearing

        self._parse_input()
        self._validate_input()

    def _load_market_data(self, risk_conf=None):
        super()._load_market_data(risk_conf)

        # these should be parsed based on ccy
        self.discounting_curve_ = self.market_data[self.discount_curve_name]
        self.forecast_curve_ = self.market_data[self.forecast_curve_name]
        self.vol_matrix_ = self.market_data[self.vol_matrix]

    def _add_fixing(self):
        SOFR_DATA_PATH = MARKET_DATA_PATH / "YIELDCURVE/Historical_SOFR_Data.xlsx"
        df = pd.read_excel(SOFR_DATA_PATH)
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])
        dates = []
        rates = []
        for _, row in df.iterrows():
            date = ql.Date(row['Effective Date'].day, row['Effective Date'].month, row['Effective Date'].year)
            rate = row['Rate']
            dates.append(date)
            rates.append(rate)
        ts = ql.RealTimeSeries(dates, rates)
        im = QLD.IndexManager.instance()
        im.setHistory("SOFRON Actual/360", ts)

    def _set_model_config(self):
        self.nb_points = 64
        self.nb_std = 7
        self.init_sigma = 0.01
        self.init_kappa = 0.02
        self.calibration_method = ql.LevenbergMarquardt()
        self.end_criteria = ql.EndCriteria(1000, 10, 1.e-8, 1.e-8, 1.e-8)

    def _validate_input(self):
        assert self.start_date < self.end_date, 'start_date must be before end_date'
        assert self.evaluation_date <= self.end_date, 'evaluation_date must be on or before end_date'

    def _parse_input(self):
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.start_date = dateParser.parse_date(self.start_date)
        self.bond_tenor = ql.Period(self.bond_tenor)
        self.calendar = tradeParser.parse_calendar(self.calendar)
        self.day_count_convention = tradeParser.parse_dc(self.day_count_convention)
        self.business_day_convention = tradeParser.parse_bdc(self.business_day_convention)
        self.currency = tradeParser.parse_ccy(self.currency)
        self.notional = float(self.notional)
        self.spread = float(self.spread)
        self.gearing = float(self.gearing)
        self.exercise_lag = int(self.exercise_lag)

        self.end_date = self.calendar.advance(self.start_date, self.bond_tenor)
        self.option_tenors = [ql.Period(t) for t in self.option_tenors]

        self.call_dates = [self.calendar.advance(self.start_date, tenor) for tenor in self.option_tenors]
        self.exercise_dates = [self.calendar.advance(call_date, -self.exercise_lag, ql.Days) for call_date in self.call_dates]  # need to parse accordingly the forecast_curve_name

    def _build_underlying(self):
        n_cf = len(self.schedule) - 1
        floating_bond = QLD.NonstandardGeneralSwap(
            ql.Swap.Receiver,
            [0.] * n_cf, [self.notional] * n_cf,
            self.schedule, [0.] * n_cf, self.day_count_convention, 0,
            self.schedule, self.index, [self.gearing] * n_cf, [self.spread] * n_cf,
            self.day_count_convention, 0, False, True
        )
        return floating_bond

    def _build_trade(self):
        n_cf = len(self.schedule) - 1
        exercise = ql.BermudanExercise(self.exercise_dates)
        n_cf_call = len(self.call_dates)
        rebated_exercise = ql.RebatedExercise(exercise, [-self.notional] * n_cf_call,
                                              self.exercise_lag, self.calendar)

        call_swap = QLD.NonstandardGeneralSwap(
            ql.Swap.Payer,
            [0.] * n_cf, [self.notional] * n_cf,
            self.schedule,
            [0.] * n_cf, self.day_count_convention,
            0,
            self.schedule,
            self.index,
            [self.gearing] * n_cf,
            [self.spread] * n_cf,
            self.day_count_convention,
            0,
            False,
            True
        )

        callable_swaption = QLD.NonstandardGeneralSwaption(call_swap, rebated_exercise)
        return callable_swaption

    def _build_engine(self, trade):
        n_cf_call = len(self.call_dates)
        gsr = ql.Gsr(self.forecast_curve_, self.exercise_dates[:-1],
                     [ql.QuoteHandle(ql.SimpleQuote(self.init_sigma))] * n_cf_call,
                     [ql.QuoteHandle(ql.SimpleQuote(self.init_kappa))] * n_cf_call)

        engine = QLD.Gaussian1dNonstandardGeneralSwaptionEngine(
            gsr, self.nb_points, self.nb_std, True, False, ql.QuoteHandle(), self.discounting_curve_)

        # calibrate
        trade.setPricingEngine(engine)
        swaption_engine = ql.Gaussian1dSwaptionEngine(gsr, self.nb_points, self.nb_std, True, False, self.discounting_curve_)
        swap_index = ql.OvernightIndexedSwapIndex(self.forecast_curve_name, self.bond_tenor, 0, self.currency, self.index)
        swap_index = swap_index.clone(self.forecast_curve_, self.discounting_curve_)
        basket = trade.calibrationBasket(swap_index, self.vol_matrix_.currentLink(), QLD.GeneralBasketGeneratingEngine.Naive)
        for basket_i in basket:
            ql.as_black_helper(basket_i).setPricingEngine(swaption_engine)
            basket_i.setPricingEngine(swaption_engine)
        gsr.calibrateVolatilitiesIterative(basket, self.calibration_method, self.end_criteria)

        return engine

    def setup(self, risk_conf=None):
        super().setup(risk_conf)
        self._add_fixing()
        self._set_model_config()

        ql.Settings.instance().evaluationDate = self.evaluation_date
        QLD.Settings.instance().evaluationDate = self.evaluation_date

    def price(self, risk_conf=None):
        self.setup(risk_conf)

        self.schedule = ql.Schedule(self.start_date, self.end_date, ql.Period(1, ql.Years),
                                    self.calendar, self.business_day_convention, self.business_day_convention,
                                    ql.DateGeneration.Forward, False)
        self.index = ql.Sofr(self.forecast_curve_)

        underlying_bond = self._build_underlying()
        engine = ql.DiscountingSwapEngine(self.discounting_curve_)
        underlying_bond.setPricingEngine(engine)
        underlying_npv = underlying_bond.NPV()

        callable_swaption = self._build_trade()
        swaption_engine = self._build_engine(callable_swaption)
        callable_swaption.setPricingEngine(swaption_engine)
        option_npv = callable_swaption.NPV()

        total_npv = underlying_npv + option_npv

        self.result['npv'] = total_npv
