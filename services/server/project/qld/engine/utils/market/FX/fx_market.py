from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql

from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.market import parseUtils
from project.qld.engine.utils.market.IR import ir_market


class FXSpot:
    def __init__(self, date, spotDate, spotRate, settlementLag, calendar, domesticCurveName, foreignCurveName, domesticCurve=None, foreignCurve=None):
        self.date = date
        self.spotDate = spotDate
        self.spotRate = spotRate
        self.settlementLag = settlementLag
        self.calendar = calendar
        self.domesticCurveName = domesticCurveName
        self.foreignCurveName = foreignCurveName
        self.domesticCurve = domesticCurve
        self.foreignCurve = foreignCurve

    def getInverse(self):
        newFXSpot = FXSpot(self.date, self.spotDate, self.spotRate, self.settlementLag, self.calendar, self.domesticCurveName, self.foreignCurveName)
        if isinstance(newFXSpot.spotRate, ql.QuoteHandle):
            orgValue = self.spotRate.value()
            if orgValue > 0.:
                newFXSpot.spotRate = ql.QuoteHandle(ql.SimpeQuote(1. / orgValue))
            else:
                raise ValueError("Cannot invert FXSpot when quote is zero or negative: " + str(orgValue))
        else:
            orgValue = self.spotRate
            if orgValue > 0.:
                newFXSpot.spotRate = 1. / orgValue
            else:
                raise ValueError("Cannot invert FXSpot when quote is zero or negative: " + str(orgValue))
        return newFXSpot

    def value(self):
        if isinstance(self.spotRate, ql.QuoteHandle):
            return self.spotRate.value()
        else:
            return self.spotRate

    def valueToday(self, marketDataFrameDictionary=None):
        spotRate = self.value()
        if marketDataFrameDictionary is not None:
            domesticCurve = marketDataFrameDictionary[self.domesticCurveName]
            foreignCurve = marketDataFrameDictionary[self.foreignCurveName]
        else:
            domesticCurve = self.domesticCurve
            foreignCurve = self.foreignCurve
        spotToday = spotRate * domesticCurve.discount(self.spotDate) / foreignCurve.discount(self.spotDate)
        return spotToday


def parseFXSpot(dfs, riskConf):
    headerTable = dfs[0]
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    calendarStr = headerTable.loc[headerTable["Key"] == "Calendar"]["Value"].values[0]
    calendar = parseUtils.parseCalendar(calendarStr)
    settlementLag = headerTable.loc[headerTable["Key"] == "SettlementLag"]["Value"].values[0]
    spotRate = headerTable.loc[headerTable["Key"] == "SpotRate"]["Value"].values[0]
    domCurveName = headerTable.loc[headerTable["Key"] == "DomesticCurve"]["Value"].values[0]
    forCurveName = headerTable.loc[headerTable["Key"] == "ForeignCurve"]["Value"].values[0]

    originalEvaluationDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "Date"]["Value"].values[0])
    originalSpotDate = du.pythonDateTime2QLDDate(headerTable.loc[headerTable["Key"] == "SpotDate"]["Value"].values[0])

    bumpObjects, dateShifts, bumpSizes = parseUtils.parseRiskConfiguration(riskConf, name)
    evaluationDate = parseUtils.bumpDateMultiple(originalEvaluationDate, dateShifts, calendar)
    spotDate = parseUtils.bumpDateMultiple(originalSpotDate, dateShifts, calendar)

    for bumpObject in bumpObjects:
        if bumpObject:
            spotRate = bumpObject.applyBump(spotRate)

    fxSpot = FXSpot(evaluationDate, spotDate, spotRate, settlementLag, calendar, domCurveName, forCurveName)
    return fxSpot


def getFXSpotInternal(fxPairStr, marketDataFrameDictionary):
    if fxPairStr in marketDataFrameDictionary:
        return marketDataFrameDictionary[fxPairStr]
    else:
        inverseFXPair = fxPairStr[3:] + fxPairStr[:3]
        if inverseFXPair in marketDataFrameDictionary:
            invFX = marketDataFrameDictionary[inverseFXPair]
            fx = invFX.getInverse()
            return fx
        else:
            raise ValueError("None of FX pairs were found: " + fxPairStr + " or " + inverseFXPair)


def getFXSpot(domStr, forStr, marketDataFrameDictionary, fxBaseCurrencyIn):
    fxBaseCurrency = fxBaseCurrencyIn if fxBaseCurrencyIn and fxBaseCurrencyIn != "" else "USD"
    domStrUpper = domStr.upper()
    forStrUpper = forStr.upper()

    if domStrUpper == fxBaseCurrency or forStrUpper == fxBaseCurrency:
        fxSpot = getFXSpotInternal(forStr + domStr, marketDataFrameDictionary)
        return fxSpot
    else:
        forBaseSpot = getFXSpotInternal(forStr + fxBaseCurrency, marketDataFrameDictionary)
        forBaseSpotRateToday = forBaseSpot.valueToday(marketDataFrameDictionary)
        baseDomSpot = getFXSpotInternal(fxBaseCurrency + domStr, marketDataFrameDictionary)
        baseDomSpotRateToday = baseDomSpot.valueToday(marketDataFrameDictionary)

        calendar = ql.JointCalendar(forBaseSpot.calendar, baseDomSpot.calendar)
        date = forBaseSpot.date
        spotDate = max(forBaseSpot.spotDate, baseDomSpot.spotDate)
        spotDate = calendar.adjust(spotDate, ql.ModifiedFollowing)
        settlementLag = max(forBaseSpot.settlementLag, baseDomSpot.settlementLag)
        forDomSpotRateToday = forBaseSpotRateToday * baseDomSpotRateToday
        domesticCurveName = baseDomSpot.domesticCurveName
        domesticCurve = marketDataFrameDictionary[domesticCurveName]
        foreignCurveName = forBaseSpot.foreignCurveName
        foreignCurve = marketDataFrameDictionary[foreignCurveName]
        spotRate = forDomSpotRateToday * foreignCurve.discount(spotDate) / domesticCurve.discount(spotDate)
        fxSpot = FXSpot(date, spotDate, spotRate, settlementLag, calendar, domesticCurveName, foreignCurveName)
        return fxSpot


def parseFXVol(dfs, riskConf, marketDataFrameDictionaryRaw):
    '''Construct FXVolSurface from inputs'''
    # Parse inputs
    headerTable = dfs[0]
    dataTable = dfs[1]
    name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
    domCcy = headerTable.loc[headerTable["Key"] == "DomesticCurrency"]["Value"].values[0]
    forCcy = headerTable.loc[headerTable["Key"] == "ForeignCurrency"]["Value"].values[0]
    domCurveName = headerTable.loc[headerTable["Key"] == "DomesticCurve"]["Value"].values[0]
    forCurveName = headerTable.loc[headerTable["Key"] == "ForeignCurve"]["Value"].values[0]
    domYCRaw = marketDataFrameDictionaryRaw[domCurveName]
    domYC = ir_market.parseYieldCurve(domYCRaw, riskConf, marketDataFrameDictionaryRaw)
    forYCRaw = marketDataFrameDictionaryRaw[forCurveName]
    forYC = ir_market.parseYieldCurve(forYCRaw, riskConf, marketDataFrameDictionaryRaw)

    fxSpotName = forCcy + domCcy
    fxSpotRaw = marketDataFrameDictionaryRaw[fxSpotName]
    fxSpot = parseFXSpot(fxSpotRaw, riskConf)
    fxSpot.domesticCurve = domYC
    fxSpot.foreignCurve = forYC

    # 2. Build FXVolSurface object
    fxSpot0 = ql.QuoteHandle(ql.SimpleQuote(fxSpot.valueToday()))
    evalDate = fxSpot.date
    settlementLag = 2  # default
    bdc = QLD.ModifiedFollowing  # business day convention is ql.ModifiedFollowing for now
    dc = QLD.Actual365Fixed()  # day counter is ql.Actual365Fixed() for now
    cal = QLD.TARGET()  # calendar is TARGET for now
    fxSpot.calendar = cal  # using TARGET for now
    timeCut = QLD.TimeCut()
    interpType = QLD.FXVolDeltaSurface.CubicSpline
    extrapType = QLD.InterpolationWithExtrapolation.LINEAR

    deltaTypes = QLD.DeltaTypeVector()
    deltaValues = []
    for c in dataTable.columns[1:6]:  # select columns 1 to 5
        if 'ATM' in c:
            deltaValues.append(0.5)
            deltaTypes.append(QLD.FXVolDeltaSurface.ATM)
        elif 'Call' in c:
            deltaValues.append(int(c[4:])/100)
            deltaTypes.append(QLD.FXVolDeltaSurface.Call)
        elif 'Put' in c:
            deltaValues.append(int(c[3:])/100)
            deltaTypes.append(QLD.FXVolDeltaSurface.Put)
        elif 'BR' in c:
            deltaValues.append(int(c[2:])/100)
            deltaTypes.append(QLD.FXVolDeltaSurface.BR)
        elif 'RR' in c:
            deltaValues.append(int(c[2:])/100)
            deltaTypes.append(QLD.FXVolDeltaSurface.RR)

    # Parse vol data table
    atmConvMap = {
        'Forward': QLD.FXVolDeltaSurface.Forward,
        'DeltaNeutral': QLD.FXVolDeltaSurface.DeltaNeutral
    }
    deltaConvMap = {
        'SpotPIPS': QLD.FXVolDeltaSurface.SpotPIPS,
        'ForwardPIPS': QLD.FXVolDeltaSurface.ForwardPIPS,
        'SpotPercent': QLD.FXVolDeltaSurface.SpotPercent,
        'ForwardPercent': QLD.FXVolDeltaSurface.ForwardPercent
    }

    optionExpiries = []
    atmConvs = QLD.ATMConventionVector()
    deltaConvs = QLD.DeltaPremiumConventionVector()
    volMatrix = ql.Matrix(dataTable.shape[0], len(deltaTypes))

    for ir, row in dataTable.iterrows():
        optionExpiries.append(cal.advance(evalDate, ql.Period(row['FXVOLSURFACE']), bdc))
        atmConvs.append(atmConvMap[row['ATMConvention']])
        deltaConvs.append(deltaConvMap[row['DeltaPremiumConvention']])
        for ic in range(len(deltaTypes)):
            volMatrix[ir][ic] = row.iloc[ic+1]  # skip first column (FXVOLSURFACE)

    # fxVolSurface object
    fxVolDeltaSurface = QLD.FXVolDeltaSurface("fxVol_delta_surface", evalDate, fxSpot0, settlementLag, cal, bdc, dc,
                                              domYC, forYC, optionExpiries, deltaTypes, deltaValues, volMatrix, atmConvs,
                                              deltaConvs, timeCut, interpType, extrapType)

    fxVolDeltaSurfaceHandle = QLD.BlackVolTermStructureHandle(fxVolDeltaSurface)
    return fxVolDeltaSurfaceHandle, fxSpot
