import pandas as pd

import project.qld.engine.parser.date as dateParser
import project.qld.engine.parser.trade as tradeParser
from project.qld.engine.qld.QLD import ql
from project.qld.engine.qld import QLD
from project.logger import get_logger

from ..base_trade import BaseTrade, MARKET_DATA_PATH

logger = get_logger(__name__)


class CallableCCS(BaseTrade):
    __name__ = "CallableCCS"

    def __init__(self, evaluation_date, start_date, end_date, cal, bdc, termination_bdc, settlement_lag,
                 dc1, dc2, ccy1, ccy2, notional_exchange, interim_exchange, notional_reset,
                 notionals1, redemption_notionals1, interim_exchange_notionals1,
                 notionals2, redemption_notionals2, interim_exchange_notionals2,
                 option_tenors, exercise_lag, freq1, freq2,
                 spread_or_fixed_rate1, spread_or_fixed_rate2, final_notional1, final_notional2):
        super().__init__(evaluation_date)
        self.start_date = start_date
        self.end_date = end_date
        self.cal = cal
        self.bdc = bdc
        self.termination_bdc = termination_bdc
        self.settlement_lag = settlement_lag
        self.dc1 = dc1
        self.dc2 = dc2
        self.ccy1 = ccy1
        self.ccy2 = ccy2
        self.notional_exchange = notional_exchange
        self.interim_exchange = interim_exchange
        self.notional_reset = notional_reset
        self.notionals1 = notionals1
        self.redemption_notionals1 = redemption_notionals1
        self.interim_exchange_notionals1 = interim_exchange_notionals1
        self.notionals2 = notionals2
        self.redemption_notionals2 = redemption_notionals2
        self.interim_exchange_notionals2 = interim_exchange_notionals2
        self.option_tenors = option_tenors
        self.exercise_lag = exercise_lag
        self.freq1 = freq1
        self.freq2 = freq2
        self.spread_or_fixed_rate1 = spread_or_fixed_rate1
        self.spread_or_fixed_rate2 = spread_or_fixed_rate2
        self.final_notional1 = final_notional1
        self.final_notional2 = final_notional2

        self._parse_input()
        self._validate_input()

    def _load_market_data(self, risk_conf=None):
        super()._load_market_data(risk_conf)

        # @TODO: import from db
        self.domYC = self.market_data["USD.SOFR.CSA_USD"]
        self.forYC = self.market_data["EUR.ESTR.CSA_USD"]
        self.forOnshoreYC = self.market_data["EUR.ESTR.CSA_EUR"]
        self.forIborYC = self.market_data["EUR.EURIBOR.6M"]
        self.domVolStructure = self.market_data["USD.SOFR.VOLMATRIX"]
        self.forVolStructure = self.market_data["EUR.ESTR.VOLMATRIX"]
        ccypair = tradeParser.get_currency_pair(self.ccy1.code(), self.ccy2.code())
        self.fxSpotObject = self.market_data[f"{ccypair}"]
        self.fxVolSurface, _ = self.market_data[f"{ccypair}.FXVOLSURFACE"]

        # fx spot
        fxSpot = self.fxSpotObject.spotRate
        spotDate = self.fxSpotObject.spotDate
        self.fxSpot0 = fxSpot * self.domYC.discount(spotDate) / self.forYC.discount(spotDate)
        self.fxSpot0Quote = ql.QuoteHandle(ql.SimpleQuote(self.fxSpot0))

        # indices
        self.index1 = ql.Sofr(self.domYC)
        self.proxyibor1 = ql.USDLibor(self.freq1, self.domYC)
        self.index2 = ql.Euribor(self.freq2, self.forOnshoreYC)

        # @TODO: parse from Input
        # [0] Domestic IR (USD SOFR)
        # [1] Foreign IR (EUR ESTR)
        # [2] FX (EURUSD)
        self.fx_ir_corr = ql.Matrix(3, 3)
        self.fx_ir_corr[0][0] = 1.0
        self.fx_ir_corr[0][1] = 0.261
        self.fx_ir_corr[0][2] = -0.218
        self.fx_ir_corr[1][0] = 0.261
        self.fx_ir_corr[1][1] = 1.0
        self.fx_ir_corr[1][2] = 0.013
        self.fx_ir_corr[2][0] = -0.218
        self.fx_ir_corr[2][1] = 0.013
        self.fx_ir_corr[2][2] = 1.0

    def _add_fixing(self):
        # Add missing fixing manually if start date is in the past
        # Source is Fed New YORK
        # Market watch https://www.newyorkfed.org/markets/reference-rates/sofr
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
        im = ql.IndexManager.instance()
        im.setHistory("SOFRON Actual/360", ts)

    def _set_model_config(self):
        self.rebateSettlementDays = 20
        self.calibrationSamples = 20000
        self.pricingSamples = 20000
        self.calibrationSeed = 42
        self.pricingSeed = 42
        self.polynomOrder = 4

    def _validate_input(self):
        assert self.start_date < self.end_date, 'start_date must be before end_date'
        assert self.evaluation_date <= self.end_date, 'evaluation_date must be on or before end_date'
        assert self.ccy1 != self.ccy2, 'ccy1 and ccy2 cannot be the same'
        assert len(self.redemption_notionals1) == len(self.option_tenors), 'redemption_notionals1 length not equal to option_tenors length'
        assert len(self.redemption_notionals2) == len(self.option_tenors), 'redemption_notionals2 length not equal to option_tenors length'
        # assert len(self.notionals1) == len(self.notionals2), 'notionals1 length not equal to notionals2 length'
        # assert len(self.notionals1) == len(self.interim_exchange_notionals1) + 1, 'notionals1 length not equal to interim_exchange_notionals1 length + 1'
        # assert len(self.notionals2) == len(self.interim_exchange_notionals2) + 1, 'notionals2 length not equal to interim_exchange_notionals2 length + 1'
        # assert all([n1 >= rn1 for n1, rn1 in zip(self.notionals1, self.redemption_notionals1)]), 'redemption_notionals1 cannot be greater than notionals1'
        # assert all([n2 >= rn2 for n2, rn2 in zip(self.notionals2, self.redemption_notionals2)]), 'redemption_notionals2 cannot be greater than notionals2'
        # assert all([n1 >= fn1 for n1, fn1 in zip(self.notionals1, [self.final_notional1]*len(self.notionals1))]), 'final_notional1 cannot be greater than any of notionals1'
        # assert all([n2 >= fn2 for n2, fn2 in zip(self.notionals2, [self.final_notional2]*len(self.notionals2))]), 'final_notional2 cannot be greater than any of notionals2'

    def _parse_notionals(self, notionals):
        ''' Ensure notionals is a list of float '''
        if isinstance(notionals, (int, float)):
            return [float(notionals)]
        elif isinstance(notionals, list):
            return [float(n) for n in notionals]
        else:
            raise ValueError('notionals must be a number or a list of numbers')

    def _parse_input(self):
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.start_date = dateParser.parse_date(self.start_date)
        self.end_date = dateParser.parse_date(self.end_date)
        self.cal = tradeParser.parse_calendar(self.cal)
        self.bdc = tradeParser.parse_bdc(self.bdc)
        self.termination_bdc = tradeParser.parse_bdc(self.termination_bdc)
        self.dc1 = tradeParser.parse_dc(self.dc1)
        self.dc2 = tradeParser.parse_dc(self.dc2)

        self.ccy1 = tradeParser.parse_ccy(self.ccy1)
        self.ccy2 = tradeParser.parse_ccy(self.ccy2)
        self.option_tenors = [ql.Period(t) for t in self.option_tenors]
        self.freq1 = ql.Period(self.freq1)
        self.freq2 = ql.Period(self.freq2)
        self.notionals1 = self._parse_notionals(self.notionals1)
        self.redemption_notionals1 = self._parse_notionals(self.redemption_notionals1)
        self.interim_exchange_notionals1 = self._parse_notionals(self.interim_exchange_notionals1)
        self.notionals2 = self._parse_notionals(self.notionals2)
        self.redemption_notionals2 = self._parse_notionals(self.redemption_notionals2)
        self.interim_exchange_notionals2 = self._parse_notionals(self.interim_exchange_notionals2)

        # exercise dates
        self.exerciseStartDates = []
        self.exerciseDates = []
        option_tenors = []
        for tenor in self.option_tenors:
            exerciseStartDate = self.cal.advance(self.start_date, tenor)
            if exerciseStartDate > self.evaluation_date:
                self.exerciseStartDates.append(exerciseStartDate)
                exerciseDate = self.cal.advance(exerciseStartDate, -self.exercise_lag, ql.Days)
                self.exerciseDates.append(exerciseDate)
                option_tenors.append(tenor)
        self.option_tenors = option_tenors

    def _build_underlying(self):
        # schedule
        sched1 = ql.Schedule(self.start_date, self.end_date, self.freq1, self.cal, self.bdc, self.termination_bdc, ql.DateGeneration.Forward, False)
        sched2 = ql.Schedule(self.start_date, self.end_date, self.freq2, self.cal, self.bdc, self.termination_bdc, ql.DateGeneration.Forward, False)

        # align notionals and schedules
        if len(self.notionals1) == 1:
            self.notionals1 = [self.notionals1[0]] * (len(sched1) - 1)
        if len(self.notionals2) == 1:
            self.notionals2 = [self.notionals2[0]] * (len(sched2) - 1)
        assert len(self.notionals1) == len(sched1) - 1, 'notionals1 length not equal to schedule1 length - 1'
        assert len(self.notionals2) == len(sched2) - 1, 'notionals2 length not equal to schedule2 length - 1'

        if len(self.interim_exchange_notionals1) == 1:
            self.interim_exchange_notionals1 = [self.interim_exchange_notionals1[0]] * (len(sched1) - 1)
        if len(self.interim_exchange_notionals2) == 1:
            self.interim_exchange_notionals2 = [self.interim_exchange_notionals2[0]] * (len(sched2) - 1)
        assert len(self.interim_exchange_notionals1) == len(sched1) - 1, 'interim_exchange_notionals1 length not equal to schedule1 length - 1'
        assert len(self.interim_exchange_notionals2) == len(sched2) - 1, 'interim_exchange_notionals2 length not equal to schedule2 length - 1'

        # counterparty pays to us interim exchange, so it comes into as a negative coupon in usd pay leg
        # we need to transfer this USD amount to leg 2 (counterparty) when we show NPV per leg later
        spreadOrFixedRates1 = [self.spread_or_fixed_rate1 - self.interim_exchange_notionals1[i] /
                               self.notionals1[i]/self.dc1.yearFraction(sched1[i], sched1[i+1]) for i in range(len(self.notionals1))]
        spreadOrFixedRates2 = [self.spread_or_fixed_rate2 - self.interim_exchange_notionals2[i] /
                               self.notionals2[i]/self.dc2.yearFraction(sched2[i], sched2[i+1]) for i in range(len(self.notionals2))]

        accret1 = self.final_notional1 / self.notionals1[-1] - 1.
        finalAccrual1 = self.dc1.yearFraction(sched1[-2], sched1[-1])
        spreadOrFixedRates1[-1] += accret1 / finalAccrual1

        accret2 = self.final_notional2 / self.notionals2[-1] - 1.
        finalAccrual2 = self.dc2.yearFraction(sched2[-2], sched2[-1])
        spreadOrFixedRates2[-1] += accret2 / finalAccrual2

        # underlying object
        ccsTradeCall = QLD.CrossCurrencySwap(
            self.ccy1, QLD.CrossCurrencySwap.Pay, QLD.CrossCurrencySwap.Float, self.notionals1, sched1, self.index1, self.dc1, spreadOrFixedRates1, 0,
            self.ccy2, QLD.CrossCurrencySwap.Receive, QLD.CrossCurrencySwap.Fixed, self.notionals2, sched2, self.index2, self.dc2, spreadOrFixedRates2, 0,
            self.notional_exchange, self.interim_exchange, self.notional_reset,
            QLD.TimeCut(),
            ql.ModifiedFollowing
        )
        return ccsTradeCall

    def _build_trade(self, ccsTradeCall):
        # Define swaption object
        bermExer = ql.BermudanExercise(self.exerciseDates)
        rebate = ql.Matrix(len(self.exerciseDates), 2)
        for i in range(len(self.exerciseDates)):
            rebate[i][0] = self.redemption_notionals1[i]
            rebate[i][1] = self.redemption_notionals2[i]
        rebatedExerc = QLD.MultiLegRebatedExercise(bermExer, rebate, self.rebateSettlementDays, self.cal, ql.ModifiedFollowing, QLD.MultiLegRebatedExercise.DummyCashflowDebug)
        ccsTradeCallOption = QLD.CrossCurrencySwaption(ccsTradeCall, rebatedExerc, QLD.Cancel, QLD.Short)
        return ccsTradeCallOption

    def _build_engine(self):
        # Define cross-asset model's parameters and cross-asset model object
        tradeTenor = ql.Period(self.end_date.year() - self.start_date.year(), ql.Years)

        # - IR vol - iniital values
        domSigma = 0.01
        domKappa = 0.01
        forSigma = 0.01
        forKappa = 0.01

        # - FX vol surface
        expiryDate = self.end_date
        fxVol = self.fxVolSurface.blackVol(expiryDate, 1.0)
        logger.debug(f'fxVol: {fxVol}')

        nExpiries = len(self.exerciseDates)
        lgm1_p = QLD.IrLgm1fPiecewiseConstantParametrization(self.ccy1, self.domYC, self.exerciseDates[:-1], [domSigma] * (nExpiries),
                                                             self.exerciseDates[:-1], [domKappa] * (nExpiries))
        lgm2_p = QLD.IrLgm1fPiecewiseConstantParametrization(self.ccy2, self.forYC, self.exerciseDates[:-1], [forSigma] * (nExpiries),
                                                             self.exerciseDates[:-1], [forKappa] * (nExpiries))
        fx_p = QLD.FxBsPiecewiseConstantParametrization(self.ccy2, self.fxSpot0Quote, self.exerciseDates[:-1], [fxVol] * (nExpiries), self.domYC)

        xasset = QLD.CrossAssetModel([lgm1_p, lgm2_p, fx_p], self.fx_ir_corr)

        # Model Calibration
        # - Domestic IR vol calibration
        domIrEngine = QLD.AnalyticLgmSwaptionEngine(xasset, 0)
        basketDom = []
        for i in range(nExpiries):
            domSmileSection = self.domVolStructure.smileSection(self.exerciseStartDates[i], tradeTenor - self.option_tenors[i])
            domAtmSwapRate = domSmileSection.atmLevel()
            domVol = domSmileSection.volatility(domAtmSwapRate)
            tempSwapHelper = ql.SwaptionHelper(
                self.exerciseDates[i], self.end_date, ql.QuoteHandle(ql.SimpleQuote(domVol)), self.proxyibor1,
                self.freq1, self.dc1, self.dc1, self.domYC,
                ql.BlackCalibrationHelper.RelativePriceError, domAtmSwapRate, 1.0, ql.Normal)
            basketDom.append(tempSwapHelper)
            basketDom[i].setPricingEngine(domIrEngine)
        method = ql.LevenbergMarquardt(1.e-8, 1.e-8, 1.e-8)
        ec = ql.EndCriteria(1000, 500, 1.e-8, 1.e-8, 1.e-8)
        xasset.calibrateIrLgm1fVolatilitiesIterative(0, basketDom, method, ec)

        # - Foreign IR vol calibration
        forIrEngine = QLD.AnalyticLgmSwaptionEngine(xasset, 1)
        basketFor = []
        for i in range(nExpiries):
            forSmileSection = self.forVolStructure.smileSection(self.exerciseStartDates[i], tradeTenor - self.option_tenors[i])
            forAtmSwapRate = forSmileSection.atmLevel()
            forVol = forSmileSection.volatility(forAtmSwapRate)
            tempSwapHelper = ql.SwaptionHelper(
                self.exerciseDates[i], self.end_date, ql.QuoteHandle(ql.SimpleQuote(forVol)), ql.Euribor(ql.Period("6M"), self.forIborYC),
                ql.Period("12M"), self.dc2, self.dc2, self.forOnshoreYC,
                ql.BlackCalibrationHelper.RelativePriceError, forAtmSwapRate, 1.0, ql.Normal)
            basketFor.append(tempSwapHelper)
            basketFor[i].setPricingEngine(forIrEngine)
        xasset.calibrateIrLgm1fVolatilitiesIterative(1, basketFor, method, ec)

        # - FX vol calibration
        ccLgmFxOptionEngineEur = QLD.AnalyticCcLgmFxOptionEngine(xasset, 0)
        ccLgmFxOptionEngineEur.cache()
        fxHelper = []
        for i in range(nExpiries):
            settleDate = self.cal.advance(self.exerciseDates[i], ql.Period("2D"))
            FXForward = self.fxSpot0 * self.forYC.discount(settleDate) / self.domYC.discount(settleDate)
            FXVol = self.fxVolSurface.blackVol(self.exerciseDates[i], FXForward)
            FXVolQuote = ql.QuoteHandle(ql.SimpleQuote(FXVol))
            tempEurUsdHelper = QLD.FxEqOptionHelper(
                self.exerciseDates[i], FXForward, self.fxSpot0Quote, FXVolQuote,
                xasset.irlgm1f(0).termStructure(),
                xasset.irlgm1f(1).termStructure())
            fxHelper.append(tempEurUsdHelper)
            fxHelper[i].setPricingEngine(ccLgmFxOptionEngineEur)
        xasset.calibrateBsVolatilitiesIterative(QLD.CrossAssetModel.AssetType_FX, 0, fxHelper, method, ec)
        fxVolCalib = xasset.fxbs(0).parameterValues(0)[0]
        logger.debug(f'fxVol Calib: {fxVolCalib}')

        xassetHandle = QLD.CrossAssetModelHandle(xasset)
        swaptionEngine = QLD.McCamXccySwaptionEngine(xassetHandle, QLD.MersenneTwisterAntithetic, QLD.MersenneTwisterAntithetic,
                                                     self.calibrationSamples, self.pricingSamples, self.calibrationSeed, self.pricingSeed, self.polynomOrder, QLD.LsmBasisSystem.Monomial)
        return swaptionEngine

    def setup(self, risk_conf=None):
        super().setup(risk_conf)
        self._add_fixing()
        self._set_model_config()

        ql.Settings.instance().evaluationDate = self.evaluation_date
        QLD.Settings.instance().evaluationDate = self.evaluation_date

    def price(self, risk_conf=None):
        # setup market, input, and model config
        self.setup(risk_conf)

        # underlying valuation
        ccsTradeCall = self._build_underlying()
        marketEngine = QLD.DiscountingXccySwapEngine(self.ccy1, self.ccy2, self.domYC, self.forYC, self.fxSpot0Quote, True)
        ccsTradeCall.setPricingEngine(marketEngine)
        underlying_npv = ccsTradeCall.NPV()
        logger.debug(f"Underlying NPV: {underlying_npv}")
        logger.debug(f"Underlying paylegNPV: {ccsTradeCall.legNPV(0)}")
        logger.debug(f"Underlying reclegNPV: {ccsTradeCall.legNPV(1)}")

        # option valuation
        ccsTradeCallOption = self._build_trade(ccsTradeCall)
        engine = self._build_engine()
        ccsTradeCallOption.setPricingEngine(engine)
        option_npv = ccsTradeCallOption.NPV()
        npvPay = ccsTradeCallOption.legNPV(0)
        npvRec = ccsTradeCallOption.legNPV(1)
        logger.debug(f"Model Call Option NPV: {option_npv}")
        logger.debug(f"Model Call Option pay leg NPV: {npvPay}")
        logger.debug(f"Model Call Option receive leg NPV: {npvRec}")

        ulNpv = ccsTradeCallOption.underlyingNPV()
        ulNpvPay = ccsTradeCallOption.underlyingLegNPV(0)
        ulNpvRec = ccsTradeCallOption.underlyingLegNPV(1)
        logger.debug(f"Model Call Option UL NPV: {ulNpv}")
        logger.debug(f"Model Call Option UL pay leg NPV: {ulNpvPay}")
        logger.debug(f"Model Call Option UL receive leg NPV: {ulNpvRec}")

        NPV = underlying_npv + option_npv

        logger.debug(f"Callable CCS NPV: {NPV}")
        self.result['npv'] = NPV
