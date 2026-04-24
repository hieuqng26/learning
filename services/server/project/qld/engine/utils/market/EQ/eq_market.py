from copy import deepcopy
import QuantLib as ql
import pandas as pd
from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql
from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.market import parseUtils
from project.qld.engine.utils.market.IR import ir_market


class EQSpot:
    def __init__(self, date, spotDate, spotPrice, settlementLag, calendar, discountingCurveName, dividendName, discountingCurve=None, dividend=None):
        self.date = date
        self.spotDate = spotDate
        self.spotPrice = spotPrice
        self.settlementLag = settlementLag
        self.calendar = calendar
        self.discountingCurveName = discountingCurveName
        self.dividendCurveName = dividendName  # need a conversion if divided is not in the form of yield but absolute amount
        self.discountingCurve = discountingCurve
        self.dividendCurve = dividend  # need a conversion if divided is not in the form of yield but absolute amount

    def value(self):
        if isinstance(self.spotPrice, ql.QuoteHandle):
            return self.spotPrice.value()
        else:
            return self.spotPrice

    def valueToday(self, marketDataFrameDictionary=None):
        spotPrice = self.value()
        if marketDataFrameDictionary is not None:
            discountingCurve = marketDataFrameDictionary[self.discountingCurveName]
            dividendCurve = marketDataFrameDictionary[self.dividendCurveName]
        else:
            discountingCurve = self.discountingCurve
            dividendCurve = self.dividendCurve
        spotToday = spotPrice * discountingCurve.discount(self.spotDate) / dividendCurve.discount(self.spotDate)
        return spotToday

    def forwardPriceBySettlementDate(self, settlementDate):
        return self.valueToday() * self.dividendCurve.discount(settlementDate) / self.discountingCurve.discount(settlementDate)

    def forwardPriceByExpiryDate(self, expiryDate):
        settlementDate = self.calendar.advance(expiryDate, ql.Period(self.settlementLag, ql.Days))
        return self.forwardPriceBySettlementDate(settlementDate)


def parseEQSpot(dfs, riskConf):
    headerTable = dfs[0]
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    calendarStr = headerTable.loc[headerTable["Key"] == "Calendar"]["Value"].values[0]
    calendar = parseUtils.parseCalendar(calendarStr)
    settlementLag = headerTable.loc[headerTable["Key"] == "SettlementLag"]["Value"].values[0]
    spotPrice = headerTable.loc[headerTable["Key"] == "SpotPrice"]["Value"].values[0]
    domCurveName = headerTable.loc[headerTable["Key"] == "DiscountingCurve"]["Value"].values[0]
    dividendName = headerTable.loc[headerTable["Key"] == "Dividend"]["Value"].values[0]

    originalEvaluationDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "Date"]["Value"].values[0])
    originalSpotDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "SpotDate"]["Value"].values[0])

    bumpObjects, dateShifts, bumpSizes = parseUtils.parseRiskConfiguration(riskConf, name)
    evaluationDate = parseUtils.bumpDateMultiple(originalEvaluationDate, dateShifts, calendar)
    spotDate = parseUtils.bumpDateMultiple(originalSpotDate, dateShifts, calendar)

    for bumpObject in bumpObjects:
        if bumpObject:
            spotPrice = bumpObject.applyBump(spotPrice)

    eqSpot = EQSpot(evaluationDate, spotDate, spotPrice, settlementLag, calendar, domCurveName, dividendName)

    if dfs[1].columns[0] == "FixingDate":
        dfFixing = dfs[1]
        dfFixing['FixingDate'] = pd.to_datetime(dfFixing['FixingDate'])
        dates = []
        prices = []
        for _, row in dfFixing.iterrows():
            date = ql.Date(row['FixingDate'].day, row['FixingDate'].month, row['FixingDate'].year)
            rate = row['Price']
            dates.append(date)
            prices.append(rate)
        ts = ql.RealTimeSeries(dates, prices)
        im_qld = QLD.IndexManager.instance()
        im_qld.setHistory(name, ts)
        im_ql = ql.IndexManager.instance()
        im_ql.setHistory(name, ts)

    return eqSpot


def parseEQDividend(dfs, riskConf, marketDataFrameDictionaryRaw):
    headerTable = dfs[0]
    dataTable = dfs[1]
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    subType = headerTable.loc[headerTable["Key"] == "SubType"]["Value"].values[0]
    if subType == "EQDividendCurve":
        dividendCurve = ir_market.parseYieldCurve(dfs, riskConf, marketDataFrameDictionaryRaw)
        return dividendCurve
    else:
        raise ValueError("Unknown SubType for Dividend: " + subType)


def parseEQVol(dfs, riskConf, marketDataFrameDictionaryRaw):
    '''Construct EQVolSurface from inputs'''
    # Parse inputs
    headerTable = dfs[0]
    dataTable = dfs[1]
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    domCcy = headerTable.loc[headerTable["Key"] == "Currency"]["Value"].values[0]
    discCurveName = headerTable.loc[headerTable["Key"] == "DiscountingCurve"]["Value"].values[0]
    dividendName = headerTable.loc[headerTable["Key"] == "Dividend"]["Value"].values[0]
    discYCRaw = marketDataFrameDictionaryRaw[discCurveName]
    discYC = ir_market.parseYieldCurve(discYCRaw, riskConf, marketDataFrameDictionaryRaw)
    dividendRaw = marketDataFrameDictionaryRaw[dividendName]
    divYC = parseEQDividend(dividendRaw, riskConf, marketDataFrameDictionaryRaw)

    eqSpotName = headerTable.loc[headerTable["Key"] == "EquitySpot"]["Value"].values[0]
    eqSpotRaw = marketDataFrameDictionaryRaw[eqSpotName]
    eqSpot = parseEQSpot(eqSpotRaw, riskConf)
    eqSpot.discountingCurve = discYC
    eqSpot.dividendCurve = divYC

    # 2. Build FXVolSurface object
    eqSpot0 = ql.QuoteHandle(ql.SimpleQuote(eqSpot.valueToday()))
    evalDate = eqSpot.date
    settlementLag = 2  # default
    bdc = QLD.ModifiedFollowing  # business day convention is ql.ModifiedFollowing for now
    dc = QLD.Actual365Fixed()  # day counter is ql.Actual365Fixed() for now
    cal = QLD.TARGET()  # calendar is TARGET for now
    eqSpot.calendar = cal  # using TARGET for now
    timeCut = QLD.TimeCut()
    interpType = QLD.FXVolDeltaSurface.CubicSpline
    # extrapType = QLD.InterpolationWithExtrapolation.WAFE
    # extrapType = QLD.InterpolationWithExtrapolation.FLAT
    extrapType = QLD.InterpolationWithExtrapolation.LINEAR

    expiryDateTimes = dataTable["EQVOLSURFACE"]
    expiryDates = []

    strikeMatrix = ql.Matrix(dataTable.shape[0], dataTable.shape[1] - 1)  # -1 is to exclude date column
    volMatrix = ql.Matrix(dataTable.shape[0], dataTable.shape[1] - 1)  # -1 is to exclude date column
    forwardPrices = []

    for i in range(strikeMatrix.rows()):
        expiryDates.append(du.pythonDateTime2QLDDate(expiryDateTimes[i]))
        forwardPrice = eqSpot.forwardPriceByExpiryDate(expiryDates[i])
        forwardPrices.append(forwardPrice)
        for j in range(strikeMatrix.columns()):
            strikeMatrix[i][j] = forwardPrice * dataTable.columns[j + 1]
            volMatrix[i][j] = dataTable.values[i][j + 1]

    # fxVolSurface object
    eqVolDeltaSurface = QLD.FXVolStrikeSurface("eqVol_strike_surface", evalDate, eqSpot0, settlementLag, cal, bdc, dc,
                                               discYC, divYC, expiryDates, strikeMatrix, volMatrix, timeCut, interpType, extrapType)

    eqVolDeltaSurfaceHandle = QLD.BlackVolTermStructureHandle(eqVolDeltaSurface)
    return eqVolDeltaSurfaceHandle, eqSpot
