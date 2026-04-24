from numpy.core.defchararray import upper
from pandas.tseries import frequencies
from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql

from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.market import parseUtils
from project.qld.engine.utils.market.FX import fx_market
from project.qld.engine.utils.market.EQ import eq_market
from project.qld.engine.utils.pricing import riskConfiguration as riskconf
import pandas as pd


def getCurrency(code):
    codeUpper = code.upper()
    if codeUpper == "USD":
        return ql.USDCurrency()
    elif codeUpper == "EUR":
        return ql.EURCurrency()
    elif codeUpper == "THB":
        return ql.THBCurrency()
    elif codeUpper == "IDR":
        return ql.IDRCurrency()
    elif codeUpper == "SEK":
        return ql.SEKCurrency()
    else:
        raise ValueError("Unknow currency: " + codeUpper)


def getOvernightIndexFromOISTicker(ticker):
    if ticker.startswith("USOSFR"):
        return ql.Sofr()
    elif ticker.startswith("JYSO"):
        return Tona()
    elif ticker.startswith('EESWE') or ticker.startswith('EUS'):
        return ql.Estr()
    elif ticker.startswith('BPSWS'):
        return ql.Sonia()
    elif ticker.startswith('THOR'):
        return Thor()
    if ticker.startswith("PZOSW"):
        return Wiron()
    if ticker.startswith("SDSOA"):
        return Sora()
    else:
        raise ValueError("Unknown ticker for OIS: " + ticker)


def getSettlementDaysFromOISTicker(ticker):
    if ticker.startswith("USOSFR"):
        # https://www.clarusft.com/sofr-swap-nuances/
        # https://www.isda.org/2023/03/27/the-final-libor-hurdle
        return 2
    elif ticker.startswith("JYSO"):
        # https://www.tokyotanshi.co.jp/en/market_data/tona/swap.html
        return 2
    elif ticker.startswith("EESWE") or ticker.startswith("EUS"):
        # https://quant.opengamma.io/Interest-Rate-Instruments-and-Market-Conventions.pdf (table 22.1 on page 48)
        return 2
    elif ticker.startswith("BPSWS"):
        # https://quant.opengamma.io/Interest-Rate-Instruments-and-Market-Conventions.pdf (table 22.1 on page 48)
        return 1
    elif ticker.startswith("THOR"):
        # https://www.bot.or.th/content/dam/bot/fmd/thor/THOR_userguide_EN.pdf (Annex 3 page 24)
        return 2
    elif ticker.startswith("PZOSW"):
        # https://www.knf.gov.pl/knf/en/komponenty/img/Recommendation_on_the_standard_OIS_transaction_based_on_WIRON_80854.pdf
        return 2
    elif ticker.startswith("SDSOA"):
        # https://www.abs.org.sg/docs/library/sora-market-compendium-on-the-transition-from-sor-to-sora-version-1-1.pdf
        # "whereas SORA OIS would have a two day payment delay"
        return 2
    else:
        raise ValueError("Unknown ticker for OIS: " + ticker)


def Tona():
    return ql.OvernightIndex("Tona", 0, ql.JPYCurrency(), ql.Japan(), ql.Actual365Fixed())

# https://www.bot.or.th/content/dam/bot/fmd/thor/THOR_userguide_EN.pdf


def Thor():
    return ql.OvernightIndex("Thor", 0, ql.THBCurrency(), ql.Thailand(), ql.Actual365Fixed())

# https://gpwbenchmark.pl/pub/BENCHMARK/files/WIRON/EN/Rules_WIRON_23.03.2023.pdf


def Wiron():
    return ql.OvernightIndex("Waron", 0, ql.PLNCurrency(), ql.Poland(), ql.Actual365Fixed())

# https://www.mas.gov.sg/-/media/mas/frn/user-guide-for-sora-index-compounded-sora-and-mas-frn.pdf


def Sora(ycHandle=None):
    cal = ql.Singapore()
    cal.addHoliday(ql.Date(31, 10, 2024))
    if ycHandle:
        return ql.OvernightIndex("Sora", 0, ql.SGDCurrency(), cal, ql.Actual365Fixed(), ycHandle)
        # return ql.OvernightIndex("Sora", 0, ql.SGDCurrency(), ql.Singapore(), ql.Actual365Fixed(), ycHandle)
    else:
        return ql.OvernightIndex("Sora", 0, ql.SGDCurrency(), cal, ql.Actual365Fixed())
        # return ql.OvernightIndex("Sora", 0, ql.SGDCurrency(), ql.Singapore(), ql.Actual365Fixed())


def getIndexFromTickerAndTenor(ticker, tenorOrDateUpper):
    if ticker.startswith("US"):
        if tenorOrDateUpper == "1D" or tenorOrDateUpper == "1BD":
            return ql.USDLiborON()
        else:
            return ql.USDLibor(ql.Period(tenorOrDateUpper))
    elif ticker.startswith("SOFRRATE"):
        return ql.Sofr()
    elif ticker.startswith("IH") or ticker.startswith("JIBOR"):
        if tenorOrDateUpper == "1D" or tenorOrDateUpper == "1BD":
            return ql.DailyTenorLibor("JIBOR", 2, ql.IDRCurrency(), ql.Indonesia(), ql.Actual360())
        else:
            return ql.Libor("JIBOR", ql.Period(tenorOrDateUpper), 2, ql.IDRCurrency(), ql.Indonesia(), ql.Actual360())
    elif ticker.startswith("TONARATE"):
        # return ql.Tona()
        return Tona()
    elif ticker.startswith("EONIARATE"):
        return ql.Eonia()
    elif ticker.startswith("ESTRRATE"):
        return ql.Estr()
    elif ticker.startswith("WIRONRATE"):
        return ql.DailyTenorLibor("WIRON", 0, ql.PLNCurrency(), ql.Poland(), ql.Actual365Fixed())
    elif ticker.startswith("JY"):
        if tenorOrDateUpper == "1D" or tenorOrDateUpper == "1BD":
            return ql.DailyTenorLibor("JPYLIBOR", 2, ql.JPYCurrency(), ql.Japan(), ql.Actual360())
        else:
            return ql.JPYLibor(ql.Period(tenorOrDateUpper))
    elif ticker.startswith("BBSW") or ticker.startswith("ADBB"):
        if tenorOrDateUpper == "1D":
            return ql.DailyTenorLibor("Bbsw", 0, ql.AUDCurrency(), ql.Australia(), ql.Actual365Fixed())
        else:
            return ql.Bbsw(ql.Period(tenorOrDateUpper))
    elif ticker.startswith("EURSW") or ticker.startswith("EURIBOR"):
        if tenorOrDateUpper == "1D":
            raise ValueError("EURIBOR overnight rate does not exist.")
        else:
            return ql.Euribor(ql.Period(tenorOrDateUpper))
    elif ticker.startswith("WIBR"):  # WIBOR for PLN
        if tenorOrDateUpper == "1D":
            return ql.DailyTenorLibor("WIBOR", 0, ql.PLNCurrency(), ql.Poland(), ql.Actual365Fixed())
        else:
            return ql.Wibor(ql.Period(tenorOrDateUpper))
    elif ticker.startswith("JIBAR"):  # JIBAR for ZAR
        if tenorOrDateUpper == "1D":
            return ql.DailyTenorLibor("JIBAR", 0, ql.ZARCurrency(), ql.SouthAfrica(), ql.Actual365Fixed())
        else:
            return ql.Jibar(ql.Period(tenorOrDateUpper))
    elif ticker.startswith("STIBOR"):  # STIBOR for SEK
        if tenorOrDateUpper == "1D":
            # https://www.riksbank.se/en-gb/statistics/swestr/background-on-swestr/
            # "a new transaction-based reference rate in Swedish kronor at the shortest maturity, overnight (O/N)"
            return ql.DailyTenorLibor("STIBOR", 0, ql.SEKCurrency(), ql.Sweden(), ql.Actual360())
        else:
            # C:\local\OpensourceRiskEngine\QuantExt\qle\indexes\ibor\sekstibor.hpp
            return ql.Libor("STIBOR", ql.Period(tenorOrDateUpper), 2, ql.SEKCurrency(), ql.Sweden(), ql.Actual360())
    else:
        raise ValueError("Unknown ticker for IBOR: " + ticker)


def getIborFromTicker(ticker):
    if ticker.startswith("ED"):  # ED for Euro-dollar futures
        return ql.USDLibor(ql.Period('3M'))
    elif ticker.startswith("EUFR") or ticker.startswith("EUR"):  # EUFR is EURIBOR FRA
        return ql.Euribor(ql.Period("3M"))
    if ticker.startswith("IR"):  # IR for AUD bank bills (BBSW) futures
        return ql.Bbsw(ql.Period('3M'))
    if ticker.startswith("PZ"):  # PZ for PLN WIBOR FRA
        return ql.Wibor(ql.Period('3M'))
    else:
        raise ValueError("Unknown ticker for IBOR futures/FRA: " + ticker)


def getFuturesTypeFromTicker(ticker):
    if ticker.startswith("ED"):  # ED for Euro-dollar futures
        return ql.Futures.IMM
    if ticker.startswith("IR"):  # IR for AUD bank bills (BBSW) futures
        return ql.Futures.ASX
    else:
        raise ValueError("Unknown ticker for IBOR futures: " + ticker)


def getIborSwapFromTicker(ticker, tenor):
    if ticker.startswith("USDSW") or ticker.startswith("USSW"):
        return ql.UsdLiborSwapIsdaFixAm(ql.Period(tenor))
    elif ticker.startswith("IDRSW") or ticker.startswith("IHSW"):  # IDRSW is temporary specified
        jibor = ql.IborIndex("Jibor", ql.Period("3M"), 2,
                             ql.IDRCurrency(), ql.Indonesia(), ql.ModifiedFollowing, False,
                             ql.Thirty360(ql.Thirty360.BondBasis))
        return ql.SwapIndex("JiborSwap", ql.Period(tenor), 2,  # settlementDays
                            ql.IDRCurrency(),
                            ql.Indonesia(),
                            ql.Period("3M"),  # fixedLegTenor
                            ql.ModifiedFollowing,  # fixedLegConvention
                            ql.Thirty360(ql.Thirty360.BondBasis),  # fixedLegDaycounter
                            jibor)
    elif ticker.startswith("EUSA"):
        return ql.EuriborSwapIsdaFixA(ql.Period(tenor))
    elif ticker.startswith("ADSWAP"):
        index = ql.IborIndex("Bbsw", ql.Period("3M"), 2,
                             ql.AUDCurrency(), ql.Australia(), ql.ModifiedFollowing, False,
                             ql.Thirty360(ql.Thirty360.BondBasis))
        return ql.SwapIndex("BbswSwap", ql.Period(tenor), 2,  # settlementDays
                            ql.AUDCurrency(),
                            ql.Australia(),
                            ql.Period("6M"),  # fixedLegTenor
                            ql.ModifiedFollowing,  # fixedLegConvention
                            ql.Thirty360(ql.Thirty360.BondBasis),  # fixedLegDaycounter
                            index)
    elif ticker.startswith("PZSW"):
        index = ql.Wibor(ql.Period("6M"))
        return ql.SwapIndex("WiborSwap", ql.Period(tenor), 2,  # settlementDays
                            ql.PLNCurrency(),
                            ql.Poland(),
                            ql.Period("1Y"),  # fixedLegTenor
                            ql.ModifiedFollowing,  # fixedLegConvention
                            ql.ActualActual(ql.ActualActual.ISDA),  # fixedLegDaycounter
                            index)
    elif ticker.startswith("SASW"):  # https://quant.opengamma.io/Interest-Rate-Instruments-and-Market-Conventions.pdf
        index = ql.Jibar(ql.Period("3M"))
        return ql.SwapIndex("JibarSwap", ql.Period(tenor), 2,  # settlementDays
                            ql.ZARCurrency(),
                            ql.SouthAfrica(),
                            ql.Period("3M"),  # fixedLegTenor
                            ql.ModifiedFollowing,  # fixedLegConvention
                            ql.Actual365Fixed(),  # fixedLegDaycounter
                            index)
    elif ticker.startswith("SEKSW"):
        index = ql.Libor("STIBOR", ql.Period("3m"), 2, ql.SEKCurrency(), ql.Sweden(), ql.Actual360())
        # https://data.bloomberglp.com/professional/sites/4/sek-stibor-fixed-to-floating-contract.pdf
        return ql.SwapIndex("StiborSwap", ql.Period(tenor), 2,  # settlementDays
                            ql.SEKCurrency(),
                            ql.Sweden(),
                            ql.Period("1Y"),  # fixedLegTenor
                            ql.ModifiedFollowing,  # fixedLegConvention
                            ql.Thirty360(ql.Thirty360.ISDA),  # fixedLegDaycounter
                            index)
    else:
        raise ValueError("Unknown ticker for IBOR swap: " + ticker)


def getIborSwapFixedLegDaycounterFromTicker(ticker):
    if ticker.startswith("USDSW") or ticker.startswith("USSW"):
        return ql.Thirty360(ql.Thirty360.BondBasis)
    elif ticker.startswith("IDRSW") or ticker.startswith("IHSW"):  # IDRSW is temporary specified
        return ql.Thirty360(ql.Thirty360.BondBasis)
    elif ticker.startswith("EUS"):  # EUR
        return ql.Thirty360(ql.Thirty360.BondBasis)
    elif ticker.startswith("ADSWAP"):
        return ql.Thirty360(ql.Thirty360.BondBasis)
    elif ticker.startswith("PZSW"):
        return ql.ActualActual(ql.ActualActual.ISDA)
    elif ticker.startswith("SASW"):  # https://quant.opengamma.io/Interest-Rate-Instruments-and-Market-Conventions.pdf
        return ql.Actual365Fixed()
    elif ticker.startswith("SEKSW"):
        return ql.Thirty360(ql.Thirty360.ISDA)
    else:
        raise ValueError("Unknown ticker for IBOR swap: " + ticker)


def parseYieldCurve(dfs, riskConf, marketDataFrameDictionaryRawForBaseCurveIfAny=None):
    headerTable = dfs[0]
    originalEvaluationDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "Date"]["Value"].values[0])
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    calendar = parseUtils.parseCalendar(headerTable.loc[headerTable["Key"] == "Calendar"]["Value"].values[0])

    bumpObjects, dateShifts, bumpSizes = parseUtils.parseRiskConfiguration(riskConf, name)
    evaluationDate = parseUtils.bumpDateMultiple(originalEvaluationDate, dateShifts, calendar)
    ql.Settings.instance().evaluationDate = evaluationDate
    QLD.Settings.instance().evaluationDate = evaluationDate

    dataTable = dfs[1]
    tickers = dataTable["TICKER"]
    types = dataTable["TYPE"]
    tenorsOrDates = dataTable["TENOR"]
    try:
        tenorsOrDates = pd.to_datetime(dataTable["TENOR"], format='%d/%m/%Y')
    except:
        tenorsOrDates = dataTable["TENOR"]
    rates = dataTable["RATE"]

    typesUpper = [t.upper() for t in types]
    if "DF" in typesUpper:
        if not all("DF" == t for t in typesUpper):
            raise ValueError("If a yield curve data contains 'DF' type, then all rows must be 'DF'.")
        else:
            quotePillarDates = []
            for tenorsOrDate in tenorsOrDates:
                if isinstance(tenorsOrDate, str):
                    tenorOrDateUpper = calendar.advance(evaluationDate, ql.Period(tenorsOrDate.upper()), ql.ModifiedFollowing, False)
                else:
                    tenorOrDateUpper = du.pythonDateTime2QLDDate(tenorsOrDate)
                    tenorOrDateUpper = parseUtils.bumpDateMultiple(tenorOrDateUpper, dateShifts, calendar)
                quotePillarDates.append(tenorOrDateUpper)

            dates = [evaluationDate] + quotePillarDates
            discountFactors = [1.0] + rates.values.tolist()
            for bumpObject in bumpObjects:
                if bumpObject:
                    if bumpObject.bumpObjectName == name and bumpObject.details and bumpObject.details.bumpRate != riskconf.BumpRate.ZeroRate:
                        raise ValueError("To bump a yield curve quoted with discount factor, only bumping zero-coupon rate is supported.")
            yieldCurve = ql.YieldTermStructureHandle(ql.DiscountCurve(dates, discountFactors, ql.Actual365Fixed()))
            yieldCurve.enableExtrapolation()
    elif "ZERO" in typesUpper:
        if not all("ZERO" == t for t in typesUpper):
            raise ValueError("If a yield curve data contains 'ZERO' type, then all rows must be 'ZERO'.")
        else:
            quotePillarDates = []
            for tenorsOrDate in tenorsOrDates:
                if isinstance(tenorsOrDate, str):
                    tenorOrDateUpper = calendar.advance(evaluationDate, ql.Period(tenorsOrDate.upper()), ql.ModifiedFollowing, False)
                else:
                    tenorOrDateUpper = du.pythonDateTime2QLDDate(tenorsOrDate)
                    tenorOrDateUpper = parseUtils.bumpDateMultiple(tenorOrDateUpper, dateShifts, calendar)
                quotePillarDates.append(tenorOrDateUpper)

            bumpedZeroRates = []
            for i in range(len(rates)):
                # bumping quote
                bumpRateSize = 0.0
                for j, bumpObject in enumerate(bumpObjects):
                    if bumpObject:
                        # if bump object specifically states zero rate, bump will be done in generic way at a later part of this parseYieldCurve() function
                        if bumpObject.details and bumpObject.details.bumpRate == riskconf.BumpRate.ZeroRate:
                            bumpRateSize += 0.0
                        else:
                            bumpRateSize += bumpObjects[j].bumpSize if bumpObjects[j].position and bumpObjects[j].bumpSize and (
                                i == bumpObjects[j].position or -1 == bumpObjects[j].position) else 0.0
                bumpedZeroRates.append(rates[i] + bumpRateSize)

            for bumpObject in bumpObjects:
                if bumpObject:
                    if bumpObject.bumpObjectName == name and bumpObject.details and bumpObject.details.bumpRate != riskconf.BumpRate.ZeroRate:
                        raise ValueError("To bump a yield curve quoted with discount factor, only bumping zero-coupon rate is supported.")
            yieldCurve = ql.YieldTermStructureHandle(ql.ZeroCurve(quotePillarDates, bumpedZeroRates, ql.Actual365Fixed(), calendar))
            yieldCurve.enableExtrapolation()
    elif "SPREAD" in typesUpper:
        if not all("SPREAD" == t for t in typesUpper):
            raise ValueError("If a yield curve data contains 'SPREAD' type, then all rows must be 'SPREAD'.")
        else:
            baseDiscountingCurveNameRow = headerTable.loc[headerTable["Key"] == "BaseDiscountingCurve"]["Value"]
            if len(baseDiscountingCurveNameRow):
                baseDiscountingCurveName = baseDiscountingCurveNameRow.values[0]
                baseDiscountingCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[baseDiscountingCurveName]
                baseDiscountingCurve = parseYieldCurve(baseDiscountingCurveRaw, riskConf, marketDataFrameDictionaryRawForBaseCurveIfAny)

                tickersUpper = [t.upper() for t in tickers]
                if all("SPZERO" == t for t in tickersUpper):
                    quotePillarDates = [calendar.advance(evaluationDate, ql.Period(tenor), ql.ModifiedFollowing, False) for tenor in tenorsOrDates]
                    spreads = [ql.QuoteHandle(ql.SimpleQuote(rate)) for rate in rates]
                    yieldCurve = ql.YieldTermStructureHandle(ql.SpreadedLinearZeroInterpolatedTermStructure(baseDiscountingCurve, spreads, quotePillarDates))
                    yieldCurve.enableExtrapolation()
                else:
                    raise ValueError("Only zero rate is supported for SPREAD instrument in parseYieldCurve()")
            else:
                raise ValueError("Base discounting curve must be given for SPREAD instrument in parseYieldCurve()")
    else:
        helpers = []
        for i in range(len(types)):
            typeUpper = types[i].upper()
            if isinstance(tenorsOrDates[i], str):
                tenorOrDateUpper = tenorsOrDates[i].upper()
            else:
                tenorOrDateUpper = du.pythonDateTime2QLDDate(tenorsOrDates[i])

            # bumping quote
            bumpRateSize = 0.0
            for j, bumpObject in enumerate(bumpObjects):
                if bumpObject:
                    if bumpObject.details and bumpObject.details.bumpRate == riskconf.BumpRate.ZeroRate:
                        bumpRateSize += 0.0
                    else:
                        bumpRateSize += bumpObjects[j].bumpSize if bumpObjects[j].position and bumpObjects[j].bumpSize and (
                            i == bumpObjects[j].position or -1 == bumpObjects[j].position) else 0.0

            # yield curve construction helper from quote
            if typeUpper == "OIS":
                index = getOvernightIndexFromOISTicker(tickers[i])
                settlementDays = getSettlementDaysFromOISTicker(tickers[i])
                helper = ql.OISRateHelper(settlementDays, ql.Period(tenorsOrDates[i]), ql.QuoteHandle(ql.SimpleQuote(rates[i] + bumpRateSize)), index, telescopicValueDates=True)
            elif typeUpper == "DEPOSIT":
                if tickers[i].upper().endswith("TN"):  # Skip T/N (tomorrow-next) because no ratehelper in QuantLib
                    continue
                else:
                    index = getIndexFromTickerAndTenor(tickers[i], tenorOrDateUpper)
                    helper = ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(rates[i] + bumpRateSize)), index)
            # Eurodollar futures quote directly linked to LIBOR rate
            # Eurodollar (SPEC): quote = 100 - LIBOR (https://www.cmegroup.com/markets/interest-rates/stirs/eurodollar.html)
            elif typeUpper == "FUTURES":
                futuresTenor = tickers[i][-1]
                if not futuresTenor.isdigit():
                    raise ValueError("Not correct ticker for IBOR futures (the last character must be digit to represent tenor) ")
                index = getIborFromTicker(tickers[i])
                futuresType = getFuturesTypeFromTicker(tickers[i])
                date = parseUtils.bumpDateMultiple(tenorOrDateUpper, dateShifts, index.fixingCalendar())
                helper = ql.FuturesRateHelper(ql.QuoteHandle(ql.SimpleQuote(rates[i] - bumpRateSize * 100.0)), date, index, ql.QuoteHandle(), futuresType)
            elif typeUpper == "FRA":
                forwardTenor = tenorsOrDates[i]
                xIndex = forwardTenor.find("x")
                if xIndex < 0 or len(forwardTenor) - 1 <= xIndex:
                    raise ValueError("Expecting tenor format like 1Mx7M, meaning starts in 1 month and finishes in 7M (so tenor is 6M)")
                startTenor = ql.Period(forwardTenor[:xIndex])
                endTenor = ql.Period(forwardTenor[(xIndex+1):])
                startMonths = int(du.monthsFromPeriod(startTenor))
                endMonths = int(du.monthsFromPeriod(endTenor))
                index = getIborFromTicker(tickers[i])
                helper = ql.FraRateHelper(ql.QuoteHandle(ql.SimpleQuote(rates[i])), startMonths, endMonths, index.fixingDays(
                ), index.fixingCalendar(), index.businessDayConvention(), index.endOfMonth(), index.dayCounter())
            elif typeUpper == "SWAP":
                swapIndex = getIborSwapFromTicker(tickers[i], "6M")  # 6M is just a dummy tenor, we only want swap convention
                headerTable = dfs[0]
                baseDiscountingCurveNameRow = headerTable.loc[headerTable["Key"] == "BaseDiscountingCurve"]["Value"]
                fixedLegDaycounter = getIborSwapFixedLegDaycounterFromTicker(tickers[i])
                if len(baseDiscountingCurveNameRow):
                    baseDiscountingCurveName = baseDiscountingCurveNameRow.values[0]
                    baseDiscountingCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[baseDiscountingCurveName]
                    baseDiscountingCurve = parseYieldCurve(baseDiscountingCurveRaw, riskConf)
                    helper = ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(rates[i] + bumpRateSize)), ql.Period(tenorOrDateUpper), swapIndex.fixingCalendar(), swapIndex.fixedLegTenor(
                    ).frequency(), swapIndex.fixedLegConvention(), fixedLegDaycounter, swapIndex.iborIndex(), ql.QuoteHandle(), ql.Period(), baseDiscountingCurve)
                else:
                    helper = ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(rates[i] + bumpRateSize)), ql.Period(tenorOrDateUpper), swapIndex.fixingCalendar(
                    ), swapIndex.fixedLegTenor().frequency(), swapIndex.fixedLegConvention(), fixedLegDaycounter, swapIndex.iborIndex(), ql.QuoteHandle(), ql.Period())
            elif typeUpper == "XCCYBASIS":
                domForecastCurveNameRow = headerTable.loc[headerTable["Key"] == "DomesticForecastingCurve"]["Value"]
                domForecastCurveName = domForecastCurveNameRow.values[0]
                domForecastCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[domForecastCurveName]
                domForecastCurve = parseYieldCurve(domForecastCurveRaw, riskConf)

                forForecastCurveNameRow = headerTable.loc[headerTable["Key"] == "ForeignForecastingCurve"]["Value"]
                forForecastCurveName = forForecastCurveNameRow.values[0]
                forForecastCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[forForecastCurveName]
                forForecastCurve = parseYieldCurve(forForecastCurveRaw, riskConf)

                baseDiscountingCurveNameRow = headerTable.loc[headerTable["Key"] == "BaseDiscountingCurve"]["Value"]
                baseDiscountingCurveName = baseDiscountingCurveNameRow.values[0]
                baseDiscountingCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[baseDiscountingCurveName]
                baseDiscountingCurve = parseYieldCurve(baseDiscountingCurveRaw, riskConf)

                # use ibor index.
                # even though ois leg, use proxy ibor
                tenor = ql.Period(tenorOrDateUpper)
                fxPairName = headerTable.loc[headerTable["Key"] == "FXSpot"]["Value"].values[0]
                ccy = headerTable.loc[headerTable["Key"] == "Currency"]["Value"].values[0]
                freqRaw = headerTable.loc[headerTable["Key"] == "Frequency"]["Value"].values[0]
                freqSpecified = ql.Period(freqRaw)
                freq = freqSpecified if freqSpecified < tenor else tenor
                domCcy = fxPairName[3:]
                forCcy = fxPairName[:3]
                fixingLag = 2
                if freq == ql.Period("1D"):
                    domProxyIbor = ql.DailyTenorLibor("domProxyIbor", fixingLag, getCurrency(domCcy), calendar, ql.Actual360(), domForecastCurve)
                    forProxyIbor = ql.DailyTenorLibor("forProxyIbor", fixingLag, getCurrency(forCcy), calendar, ql.Actual360(), forForecastCurve)
                else:
                    domProxyIbor = ql.Libor("domProxyIbor", freq, fixingLag, getCurrency(domCcy), calendar, ql.Actual360(),
                                            domForecastCurve) if domCcy.upper() != "EUR" else ql.EURLibor(freq, domForecastCurve)
                    forProxyIbor = ql.Libor("forProxyIbor", freq, fixingLag, getCurrency(forCcy), calendar, ql.Actual360(),
                                            forForecastCurve) if forCcy.upper() != "EUR" else ql.EURLibor(freq, forForecastCurve)

                bdc = ql.ModifiedFollowing
                currency = headerTable.loc[headerTable["Key"] == "Currency"]["Value"].values[0]
                isFxBasedOnDomesticCurrency = isFxTargetOnForeignCurrency = currency == fxPairName[:3]
                isBasisOnFxBaseCurrencyLeg = not isFxBasedOnDomesticCurrency
                baseIndex = domProxyIbor
                quoteIndex = forProxyIbor

                helper = ql.ConstNotionalCrossCurrencyBasisSwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(
                    rates[i])), tenor, fixingLag, calendar, bdc, False, baseIndex, quoteIndex, baseDiscountingCurve, isFxBasedOnDomesticCurrency, isBasisOnFxBaseCurrencyLeg)
            elif typeUpper == "FXFWDPOINT" or typeUpper == "FXFWD":
                fxPairName = headerTable.loc[headerTable["Key"] == "FXSpot"]["Value"].values[0]
                fxSpotRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[fxPairName]
                fxSpot = fx_market.parseFXSpot(fxSpotRaw, riskConf)
                fxSpotValue = fxSpot.value()
                fxSpotQutoeHandle = ql.QuoteHandle(ql.SimpleQuote(fxSpotValue))
                fxFwdPt = rates[i] - (fxSpotValue if typeUpper == "FXFWD" else 0.)
                fxFwdPtQuoteHandle = ql.QuoteHandle(ql.SimpleQuote(fxFwdPt))

                baseDiscountingCurveNameRow = headerTable.loc[headerTable["Key"] == "BaseDiscountingCurve"]["Value"]
                baseDiscountingCurveName = baseDiscountingCurveNameRow.values[0]
                baseDiscountingCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[baseDiscountingCurveName]
                baseDiscountingCurve = parseYieldCurve(baseDiscountingCurveRaw, riskConf)

                spotLag = fxSpotRaw[0].loc[fxSpotRaw[0]["Key"] == "SettlementLag"]["Value"].values[0]
                # bdc = fxSpotRaw[0].loc[fxSpotRaw[0]["Key"]=="BusinessDayConvention"]["Value"].values[0]
                bdc = ql.ModifiedFollowing
                currency = headerTable.loc[headerTable["Key"] == "Currency"]["Value"].values[0]
                isFxBasedOnDomesticCurrency = isFxTargetOnForeignCurrency = currency == fxPairName[3:]
                helper = ql.FxSwapRateHelper(fxFwdPtQuoteHandle, fxSpotQutoeHandle, ql.Period(tenorsOrDates[i]),
                                             2, calendar, bdc, False, isFxBasedOnDomesticCurrency, baseDiscountingCurve)
            elif typeUpper == "EQFWD":
                eqSpotName = headerTable.loc[headerTable["Key"] == "EQSpot"]["Value"].values[0]
                eqSpotRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[eqSpotName]
                eqSpot = eq_market.parseEQSpot(eqSpotRaw, riskConf)
                eqSpotValue = eqSpot.value()
                eqSpotQutoeHandle = ql.QuoteHandle(ql.SimpleQuote(eqSpotValue))
                eqFwdPt = rates[i] - eqSpotValue
                eqFwdPtQuoteHandle = ql.QuoteHandle(ql.SimpleQuote(eqFwdPt))

                discountingCurveNameRow = headerTable.loc[headerTable["Key"] == "DiscountingCurve"]["Value"]
                discountingCurveName = discountingCurveNameRow.values[0]
                discountingCurveRaw = marketDataFrameDictionaryRawForBaseCurveIfAny[discountingCurveName]
                discountingCurve = parseYieldCurve(discountingCurveRaw, riskConf)

                spotLag = eqSpotRaw[0].loc[eqSpotRaw[0]["Key"] == "SettlementLag"]["Value"].values[0]
                # bdc = fxSpotRaw[0].loc[fxSpotRaw[0]["Key"]=="BusinessDayConvention"]["Value"].values[0]
                bdc = ql.ModifiedFollowing
                days = calendar.businessDaysBetween(evaluationDate, du.pythonDateTime2QLDDate(tenorsOrDates[i]))
                helper = ql.FxSwapRateHelper(eqFwdPtQuoteHandle, eqSpotQutoeHandle, ql.Period(days, ql.Days),
                                             2, calendar, bdc, False, False, discountingCurve)
            else:
                raise Exception("Unknown instrument type: " + typeUpper + " in yield curve (" + name + ") creation")
            helpers.append(helper)

        quotePillarDates = [helper.pillarDate() for helper in helpers]
        yieldCurve = ql.YieldTermStructureHandle(ql.PiecewiseLinearZero(evaluationDate, helpers, ql.Actual365Fixed()))
        yieldCurve.enableExtrapolation()

    # bump internal zero rate
    for j, bumpObject in enumerate(bumpObjects):
        if bumpObject:
            if bumpObject.details and bumpObject.details.bumpRate == riskconf.BumpRate.ZeroRate:
                if bumpObject.details.zeroRateBumpTenors == None:
                    pillarDates = quotePillarDates
                else:
                    earliestDate = quotePillarDates[0]
                    pillarDates = [calendar.advance(earliestDate, ql.Period(tenor), ql.ModifiedFollowing, False) for tenor in bumpObject.details.zeroRateBumpTenors]
                    # pillarDates = [index.fixingCalendar().advance(earliestDate, ql.Period(tenor), ql.ModifiedFollowing, False) for tenor in bumpObject.details.zeroRateBumpTenors]
                if bumpObject.bumpType == riskconf.BumpType.Absolute:
                    pillarBumps = [ql.QuoteHandle(ql.SimpleQuote(bumpObject.bumpSize)) if bumpObject.position == -1 or bumpObject.position ==
                                   i else ql.QuoteHandle(ql.SimpleQuote(0.0)) for i in range(len(pillarDates))]
                elif bumpObject.bumpType == riskconf.BumpType.Relative:
                    pillarBumps = []
                    for i in range(len(pillarDates)):
                        if bumpObject.position == -1 or bumpObject.position == i:
                            zeroRate = yieldCurve.zeroRate(pillarDates[i], ql.Actual365Fixed(), ql.Continuous).rate()
                            quote = ql.QuoteHandle(ql.SimpleQuote(zeroRate * bumpObject.bumpSize))
                        else:
                            quote = ql.QuoteHandle(ql.SimpleQuote(0.0))
                        pillarBumps.append(quote)
                else:
                    raise ValueError("Unknown bump type: " + str(riskConf.bumpType))
                yieldCurve = ql.YieldTermStructureHandle(ql.SpreadedLinearZeroInterpolatedTermStructure(yieldCurve, pillarBumps, pillarDates))
                yieldCurve.enableExtrapolation()

    return yieldCurve


def parseIRVol(dfs, riskConf, marketDataFrameDictionaryRaw):
    headerTable = dfs[0]
    originalEvaluationDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "Date"]["Value"].values[0])
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    subType = headerTable.loc[headerTable["Key"] == "SubType"]["Value"].values[0]
    calendar = parseUtils.parseCalendar(headerTable.loc[headerTable["Key"] == "Calendar"]["Value"].values[0])

    # fetch yield curve
    DiscountCurveName = headerTable.loc[headerTable["Key"] == "DiscountCurve"]["Value"].values[0]
    DiscountCurveRaw = marketDataFrameDictionaryRaw[DiscountCurveName]
    DiscountCurve = parseYieldCurve(DiscountCurveRaw, riskConf, marketDataFrameDictionaryRaw)
    ForecastCurveName = headerTable.loc[headerTable["Key"] == "ForecastCurve"]["Value"].values[0]
    # As long as we use RFR, we don't use ForecastCurve though
    if ForecastCurveName == "":
        ForecastCurveName = DiscountCurveName
        ForecastCurveRaw = DiscountCurveRaw
        ForecastCurve = DiscountCurve
    else:
        ForecastCurveRaw = marketDataFrameDictionaryRaw[ForecastCurveName]
        ForecastCurve = parseYieldCurve(ForecastCurveRaw, riskConf, marketDataFrameDictionaryRaw)

    if subType == "IRVolMatrix":
        # print("a") # dummy line
        # TODO:
        # Set variables below:

        swapTenors = dfs[1].columns.tolist()
        swapTenors = swapTenors[1:]
        optionTenors = dfs[1].iloc[:, 0].tolist()
        atmVols = dfs[1].iloc[:, 1:]
        optionTenors = [ql.Period(tenor) for tenor in optionTenors]
        swapTenors = [ql.Period(tenor) for tenor in swapTenors]
        dayCounts = ql.Actual365Fixed()
        volType = ql.Normal if dfs[0].loc[dfs[0]['Key'] == 'VolType', 'Value'].values[0].upper() == "NORMAL" else ql.ShiftedLognormal
        atmVols = atmVols.to_numpy().tolist()

        # - optionTenors as ql.Period from DataFrame dfs
        # - swapTernos as ql.Period from DataFrame dfs
        # - atmVols matrix from DataFrame dfs
        # - dayCounts, let us set ql.Actual365Fixed() for now
        # - volType from DataFrame dfs
        # and comment out below to return vol object
        # refer to C:\local\ql_build\QLD\QLD-Python\projects\P202208\market\IR\volatilitycube.py

        swaptionAtmVolMatrix = ql.SwaptionVolatilityMatrix(
            calendar, ql.ModifiedFollowing,
            optionTenors, swapTenors, ql.Matrix(atmVols),
            dayCounts, False, volType)

        volAtmMatrixHdl = ql.SwaptionVolatilityStructureHandle(swaptionAtmVolMatrix)
        volAtmMatrixHdl.enableExtrapolation()
        return volAtmMatrixHdl
    else:
        raise ValueError("Unsupported SubType of IRVol: " + subType)
    return 0
