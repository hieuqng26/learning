from copy import deepcopy
from datetime import datetime
import os
import pandas as pd
import time
import multiprocessing as mp

from project.qld.engine.qld import QLD
from project.logger import get_logger

logger = get_logger(__name__)
from project.qld.engine.qld.QLD import ql
from project.qld.engine.utils.market import marketTools
from project.qld.engine.utils.market import parseUtils
from project.qld.engine.utils.market.FX import fx_market
from project.qld.engine.utils.trade import generalTrade
from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.pricing import riskConfiguration as riskconf
from project.qld.engine.utils.pricing.FX import fx_pricing
from project.qld.engine.utils.tools import qld_file


class Result(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        pd.DataFrame.__init__(self, *args, **kwargs, columns=['tradeID', 'riskConfiguration', 'value', 'details', 'extra'])


class ResultString(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        pd.DataFrame.__init__(self, *args, **kwargs, columns=['tradeID', 'riskType', 'riskBumpObjectNames', 'riskBumpPositions', 'value', 'details', 'extra'])


def computeSingle(tradeDataFrame, marketDataFrameDictionaryRaw, pricingSettings, riskConf):
    tradeID = tradeDataFrame["TradeID"][0]

    # parse market data, and make all bump if specified
    marketDataFrameDictionary = marketTools.parseMarketDataFrameDictionary(marketDataFrameDictionaryRaw, riskConf)

    fxBaseCurrency = pricingSettings["FXBaseCurrency"]
    evaluationDate = du.pythonDateTime2QLDDate(marketDataFrameDictionary["Date"])
    ql.Settings.instance().evaluationDate = evaluationDate
    QLD.Settings.instance().evaluationDate = evaluationDate
    if tradeDataFrame["Calculate"][0]:
        tradeType = tradeDataFrame["TradeType"][0]
        trade = generalTrade.parseTrades(tradeDataFrame, marketDataFrameDictionary)[0]
        if tradeType == "IRSwap":
            discountCurve = marketDataFrameDictionary[tradeDataFrame.Discounting[0]]
            forecastCurve = marketDataFrameDictionary[tradeDataFrame.FloatIndex[0]]
            engine = ql.DiscountingSwapEngine(discountCurve)
            pricedCurrency = tradeDataFrame["NotionalCurrency"][0]

        elif tradeType == "IROISwap":  # add branch for OIS SWAP
            discountCurve = marketDataFrameDictionary[tradeDataFrame.Discounting[0]]
            forecastCurve = marketDataFrameDictionary[tradeDataFrame.OvernightIndex[0]]
            engine = ql.DiscountingSwapEngine(discountCurve)
            pricedCurrency = tradeDataFrame["NotionalCurrency"][0]

        elif tradeType == "IRFixedRateBond" or tradeType == "IRFloatingRateBond":
            discountCurve = marketDataFrameDictionary[tradeDataFrame.Discounting[0]]
            engine = ql.DiscountingBondEngine(discountCurve)
            pricedCurrency = tradeDataFrame["NotionalCurrency"][0]

        elif tradeType == "FXForward" or tradeType == "FXSpot":
            # fxSpotRate = marketDataFrameDictionary[tradeDataFrame.ForeignCurrency[0] + tradeDataFrame.DomesticCurrency[0]]
            fxSpot = fx_market.getFXSpot(tradeDataFrame.DomesticCurrency[0], tradeDataFrame.ForeignCurrency[0], marketDataFrameDictionary, fxBaseCurrency)
            domesticCurve = marketDataFrameDictionary[tradeDataFrame.DomesticDiscounting[0]]
            foreignCurve = marketDataFrameDictionary[tradeDataFrame.ForeignDiscounting[0]]
            engine = fx_pricing.DiscountingFXForwardEngine(fxSpot, domesticCurve, foreignCurve)
            pricedCurrency = tradeDataFrame["DomesticCurrency"][0]

        elif tradeType == "FXVanillaOption":
            fxSpot = fx_market.getFXSpot(tradeDataFrame.DomesticCurrency[0], tradeDataFrame.ForeignCurrency[0], marketDataFrameDictionary, fxBaseCurrency)
            domesticCurve = marketDataFrameDictionary[tradeDataFrame.DomesticDiscounting[0]]
            foreignCurve = marketDataFrameDictionary[tradeDataFrame.ForeignDiscounting[0]]
            fxVolSurface = marketDataFrameDictionary[tradeDataFrame.FXVolSurface[0]]
            engine = fx_pricing.BlachSholesFXVanillaOptionEngine(fxSpot, domesticCurve, foreignCurve, fxVolSurface)
            pricedCurrency = tradeDataFrame["DomesticCurrency"][0]
        else:
            raise ValueError("Unknown trade type " + str(tradeType))
        trade.setPricingEngine(engine)
        value = trade.NPV()

        fxSpotTodayPricedToReporting = 1.
        reportingCcy = pricingSettings["ReportingCurrency"]
        if reportingCcy and reportingCcy != pricedCurrency:
            fxSpotPricedToReporting = fx_market.getFXSpot(reportingCcy, pricedCurrency, marketDataFrameDictionary, fxBaseCurrency)
            fxSpotTodayPricedToReporting = fxSpotPricedToReporting.valueToday(marketDataFrameDictionary)
            # fxasset.fxspot(baseMarketPath, "xlsx", pricingSettings["ReportingCurrency"], tradeDataFrame["NotionalCurrency"][0], evaluationDate, riskConf)
        value = value * fxSpotTodayPricedToReporting
        result = Result({'tradeID': [tradeID], 'riskConfiguration': [riskConf], 'value': [value]})
        if tradeType == 'IROISwap':
            result['extra'] = [f'FixedLeg:{trade.legNPV(0) * fxSpotTodayPricedToReporting}, ' +
                               f'OvernightLeg:{trade.legNPV(1) * fxSpotTodayPricedToReporting}']
        return result


def computeTrade(riskConfigurations, marketDataFrameDictionaryRaw, tradeColumns, tradeValues, pricingSettings, timestamp, outputPath):
    # riskConfigurations = riskconf.parseRiskConfs(riskConfigurations)
    tradeDataFrame = pd.DataFrame([tradeValues], columns=tradeColumns, index=None)
    resultSingles = []
    for riskConf in riskConfigurations:
        # result class has columns of tradeID, riskConf, value, details
        resultSingle = computeSingle(tradeDataFrame, marketDataFrameDictionaryRaw, pricingSettings, riskConf)
        resultSingles.append(resultSingle)

    bumpObjectNames = []
    bumpObjectPositionsStr = []
    bumpObjectDetailssStr = []
    if riskConfigurations[0] and riskConfigurations[0].bumpObjects:
        for bumpObject in riskConfigurations[0].bumpObjects:
            bumpObjectNames.append(bumpObject.bumpObjectName)
            bumpObjectPositionsStr.append(str(bumpObject.position))
            bumpObjectDetailssStr.append(str(bumpObject.details.returnString if bumpObject.details and bumpObject.details.returnString else ""))
            # bumpObjectDetailssStr.append("")

    risk_result = ResultString({'tradeID': [resultSingles[0].tradeID[0]],
                                'riskType': [resultSingles[0].riskConfiguration[0].riskType],
                                'riskBumpObjectNames': [" ".join(bumpObjectNames)],
                                'riskBumpPositions': [" ".join(bumpObjectPositionsStr)],
                                'value': [0.0],
                                'details': [" ".join(bumpObjectDetailssStr)],
                                'extra': [""]})
    for idx, riskConf in enumerate(riskConfigurations):
        multiplier = 1.0 if riskConf.riskType == riskconf.RiskType.NPV else riskConf.multiplier
        risk_result.value += resultSingles[idx].value * multiplier
        risk_result.extra += resultSingles[idx].extra

    header = ", ".join(risk_result.columns)
    result_risk_str = [str(risk_result[column][0]) for column in risk_result]
    outputStr = ", ".join(["None" if entry == "" else entry for entry in result_risk_str])

    doOutputConsole = True
    if doOutputConsole:
        logger.info(outputStr)

    doOutputFile = True
    if doOutputFile:
        filenameForRiskBumpObjectNames = "_" + str(risk_result["riskBumpObjectNames"][0]) if risk_result["riskBumpObjectNames"][0] else ""
        tradeFileNameNoExtension = os.path.splitext(tradeDataFrame["filename"][0])[0]
        filename = tradeFileNameNoExtension + "_" + str(risk_result["riskType"][0]) + filenameForRiskBumpObjectNames + "_" + timestamp + ".txt"
        filename = outputPath + "/" + filename
        if os.path.isfile(filename):
            f = open(filename, "a")
            f.write(outputStr + "\n")
        else:
            f = open(filename, "w")
            f.write(header + "\n")
            f.write(outputStr + "\n")
    return {"filename": filename if doOutputFile else None}


def relevantRiskPositions(parallelOrBucket, bumpObjectName, marketDataFrameDictionary, dfTrade, positionAlignedWithTrade, details, pricingSettings):
    # @HO: in the future, we should implement a tracing mechanism
    # 1. Compute a base PV and recoord which market object quotes are used in the pricing. Record form is like a dictionary {marketObjectName, [expiryTenora, swapTenors. ]}
    # 2. Use the dictionary for risk bump
    # However, because it has to replace market objects in QuantLib with derived classes in QLD with tracing mechanism, we put it as a future project
    # This mechanism will be important when we use two models for the same products like HW vs LMM
    #
    # Complicated point in this approach is to bump arbitrary tenors on zero coupon rate in yield curve.
    # After obtain a dictionary for the quote instruments, we determined by time from valuation date
    #
    # For now, we implement a dirty way -- determines tenor for each product.

    reportingCcy = pricingSettings["ReportingCurrency"]
    baseCcy = pricingSettings["FXBaseCurrency"]
    notionalCcy = dfTrade.NotionalCurrency
    notFXBaseReportingBump = (bumpObjectName != reportingCcy + baseCcy) and (bumpObjectName != baseCcy + reportingCcy)

    # If the bump object clearly does not have impect on the trade, return empty array
    tradeType = dfTrade.TradeType
    if tradeType == "IRSwap":
        fXNotionalRepoting = notionalCcy + baseCcy
        fxBaseNotional = baseCcy + notionalCcy
        # if bumpObjectName != dfTrade.FloatIndex and bumpObjectName != dfTrade.Discounting and bumpObjectName != fXNotionalRepoting and bumpObjectName != fxBaseNotional and notFXBaseReportingBump:
        if bumpObjectName != dfTrade.FloatIndex \
                and not marketTools.isRelevantBumpObjectToTradeMarketObject(bumpObjectName, dfTrade.Discounting, marketDataFrameDictionary) \
                and bumpObjectName != fXNotionalRepoting and bumpObjectName != fxBaseNotional and notFXBaseReportingBump:
            return []
    elif tradeType == "IROISwap":
        fXNotionalRepoting = notionalCcy + baseCcy
        fxBaseNotional = baseCcy + notionalCcy
        if bumpObjectName != dfTrade.OvernightIndex \
                and not marketTools.isRelevantBumpObjectToTradeMarketObject(bumpObjectName, dfTrade.Discounting, marketDataFrameDictionary) \
                and bumpObjectName != fXNotionalRepoting and bumpObjectName != fxBaseNotional and notFXBaseReportingBump:
            return []
    elif tradeType == "IRFixedRateBond":
        fXNotionalRepoting = notionalCcy + baseCcy
        fxBaseNotional = baseCcy + notionalCcy
        # if bumpObjectName != dfTrade.Discounting \
        if not marketTools.isRelevantBumpObjectToTradeMarketObject(bumpObjectName, dfTrade.Discounting, marketDataFrameDictionary) \
                and bumpObjectName != fXNotionalRepoting and bumpObjectName != fxBaseNotional and notFXBaseReportingBump:
            return []
    elif tradeType == "FXForward" or tradeType == "FXSpot":
        domCcy = dfTrade.DomesticCurrency
        forCcy = dfTrade.ForeignCurrency
        fXDomBas = domCcy + baseCcy
        fxBasDom = baseCcy + domCcy
        fxForBas = forCcy + baseCcy
        fXBasFor = baseCcy + forCcy
        # if bumpObjectName != dfTrade.DomesticDiscounting and bumpObjectName != dfTrade.ForeignDiscounting \
        if not marketTools.isRelevantBumpObjectToTradeMarketObject(bumpObjectName, dfTrade.DomesticDiscounting, marketDataFrameDictionary) \
           and not marketTools.isRelevantBumpObjectToTradeMarketObject(bumpObjectName, dfTrade.ForeignDiscounting, marketDataFrameDictionary) \
           and bumpObjectName != fXDomBas and bumpObjectName != fxBasDom \
           and bumpObjectName != fxForBas and bumpObjectName != fXBasFor and notFXBaseReportingBump:
            return []

    # choose tenor
    if parallelOrBucket == "Parallel":
        return [-1]
    elif parallelOrBucket == "Bucket":
        riskPositions = []
        marketObjectToBump = marketDataFrameDictionary[bumpObjectName]
        headerTable = marketObjectToBump[0]
        category = headerTable.loc[headerTable["Key"] == "Category"]["Value"].values[0]
        if category == "Market":
            marketType = headerTable.loc[headerTable["Key"] == "Type"]["Value"].values[0]
        else:
            marketType = None

        if marketType == "FXSpot":
            return [-1]
        elif marketType == "YieldCurve":
            if details and details.bumpRate == riskconf.BumpRate.ZeroRate and details.zeroRateBumpTenors:
                tenorsOrDates = details.zeroRateBumpTenors
            else:
                tenorsOrDates = marketObjectToBump[1]["TENOR"]
            maxLineIndex = len(tenorsOrDates)

            if not positionAlignedWithTrade:
                # cover all lines
                return list(range(maxLineIndex))
            else:
                # take only relevant lines
                tradeType = dfTrade.TradeType
                if tradeType == "IRSwap" or tradeType == "IRFixedRateBond":
                    startDate = du.pythonDateTime2QLDDate(dfTrade.StartDate)
                    endDateOrTenor = dfTrade.EndDateOrTenor
                    if isinstance(endDateOrTenor, str):
                        endTenor = ql.Period(endDateOrTenor)
                        endDate = calendar.advance(evaluationDate, endTenor)
                    else:
                        endDate = du.pythonDateTime2QLDDate(endDateOrTenor)
                elif tradeType == "FXForward" or tradeType == "FXSpot":
                    startDate = du.pythonDateTime2QLDDate(dfTrade.SettlementDateOrTenor)
                    endDate = startDate

                evaluationDate = du.pythonDateTime2QLDDate(marketObjectToBump[0].loc[marketObjectToBump[0].Key == "Date"].Value.values[0])
                calendar = parseUtils.parseCalendar(marketObjectToBump[0].loc[marketObjectToBump[0].Key == "Calendar"].Value.values[0])
                riskDates = []
                quoteDates = []
                for i in range(maxLineIndex):
                    if isinstance(tenorsOrDates[i], str):
                        tenor = ql.Period(tenorsOrDates[i])
                        date = calendar.advance(evaluationDate, tenor)
                    else:
                        date = du.pythonDateTime2QLDDate(tenorsOrDates[i])
                    quoteDates.append(date)
                    if startDate <= date and date <= endDate:
                        riskPositions.append(i)
                        riskDates.append(date)
                if quoteDates[-1] < startDate:
                    riskPositions = list(range(maxLineIndex))
                    riskDates = quoteDates
                if evaluationDate <= endDate and endDate < quoteDates[0]:
                    riskPositions = [0]
                    riskDates = [quoteDates[0]]

                if riskPositions and startDate < riskDates[0] and riskPositions[0] > 0:
                    riskPositions.insert(0, riskPositions[0] - 1)  # to sort riskPositions for ease of debugging
                if riskPositions and riskDates[-1] < endDate and riskPositions[-1] < maxLineIndex - 1:
                    riskPositions.append(riskPositions[-1] + 1)

                return riskPositions
        else:
            raise NotImplementedError

    else:
        raise NotImplementedError


def generateRiskConfigurationssForTrade(fileDFs, marketDataFrameDictionaryRaw, dfTrade, pricingSettings):
    riskConfss = []
    for i in range(1, len(fileDFs)):
        riskConfs = []
        fileDFs_i = fileDFs[i]
        dc = fileDFs_i.set_index("Key").loc[:, "Value"].to_dict()
        # risk sensitivities
        if dc["Type"] == "RiskConfiguration":
            riskType = riskconf.RiskType[dc["RiskType"]]
            if riskType == riskconf.RiskType.NPV:
                riskConfs = [riskconf.RiskConfiguration(riskType, None, 1.0)]
                riskConfss.append(riskConfs)
            else:
                parallelOrBucket = dc["ParallelOrBucket"]
                positionAlignedWithTrade = dc["PositionAlignedWithTrade"]
                nBumpLines = dc["nBumpLines"]
                if nBumpLines:
                    idxBumpLines = fileDFs_i.loc[fileDFs_i["Key"] == "nBumpLines"].index.values[0]
                    firstRiskRowIdx = idxBumpLines + 1
                    positionss = []
                    bumpObjectTemplates = []
                    riskConfTemplates = []
                    for idx in range(firstRiskRowIdx, len(fileDFs_i)):
                        iRiskConf = fileDFs_i["Key"][idx]
                        iBumpConf = fileDFs_i["Value"][idx]
                        bumpObjectName = fileDFs_i["BumpObject"][idx]
                        bumpSize = fileDFs_i["BumpSize"][idx]
                        bumpType = riskconf.BumpType[fileDFs_i["BumpType"][idx]]
                        multiplier = fileDFs_i["Multiplier"][idx]
                        details = riskconf.BumpDetails(fileDFs_i["Details"][idx])
                        positions = relevantRiskPositions(parallelOrBucket, bumpObjectName, marketDataFrameDictionaryRaw,
                                                          dfTrade, positionAlignedWithTrade, details, pricingSettings)
                        bumpObjectTemplate = riskconf.BumpObject(bumpObjectName, None, bumpSize, bumpType, details)
                        bumpObjectTemplates.append(bumpObjectTemplate)
                        positionss.append(positions)

                        if idx == len(fileDFs_i)-1 or fileDFs_i["Value"][idx+1] == 0:
                            riskConfTemplates.append(riskconf.RiskConfiguration(riskType, deepcopy(bumpObjectTemplates), multiplier))
                            bumpObjectTemplates = []
                            positionss_this_riskConfTemplate = positionss
                            positionss = []

                    # riskConfs = deepcopy(riskConfTemplates)
                    if len(positionss_this_riskConfTemplate) == 1:
                        for p0 in positionss_this_riskConfTemplate[0]:
                            riskConfs = deepcopy(riskConfTemplates)
                            for riskConf in riskConfs:
                                riskConf.bumpObjects[0].position = p0
                                details0 = riskConf.bumpObjects[0].details
                                if details0 and isinstance(details0, riskconf.BumpDetails) and details0.bumpRate == riskconf.BumpRate.ZeroRate and details0.zeroRateBumpTenors and (not details0.returnString):
                                    details0.returnString = details0.zeroRateBumpTenors[p0]
                            riskConfss.append(deepcopy(riskConfs))
                    elif len(positionss_this_riskConfTemplate) == 2:
                        for p0 in positionss_this_riskConfTemplate[0]:
                            for p1 in positionss_this_riskConfTemplate[1]:
                                riskConfs = deepcopy(riskConfTemplates)
                                for riskConf in riskConfs:
                                    riskConf.bumpObjects[0].position = p0
                                    riskConf.bumpObjects[1].position = p1
                                    details0 = riskConf.bumpObjects[0].details
                                    if details0 and isinstance(details0, riskconf.BumpDetails) and details0.bumpRate == riskconf.BumpRate.ZeroRate and details0.zeroRateBumpTenors and (not details0.returnString):
                                        details0.returnString = details0.zeroRateBumpTenors[p0]
                                    details1 = riskConf.bumpObjects[0].details
                                    if details1 and isinstance(details1, riskconf.BumpDetails) and details1.bumpRate == riskconf.BumpRate.ZeroRate and details1.zeroRateBumpTenors and (not details1.returnString):
                                        details1.returnString = details1.zeroRateBumpTenors[p1]
                                riskConfss.append(deepcopy(riskConfs))
                    else:
                        raise NotImplementedError
    return riskConfss


def computePriceRisk(tradeFilenameOrPath, baseMarketPath, basePricingPath, outputPath, doParallel):
    argss = []
    timestamp = str(datetime.now()).replace(" ", "T").replace(":", "").replace("-", "")

    marketDataFrameDictionary = marketTools.loadMarketDataFrameDirectory(baseMarketPath)
    # marketDataDictionary = marketTools.parseMarketDataFrameDictionary(marketDataFrameDictionary)
    dfTradesAggregated = generalTrade.loadTradesDataFrames(tradeFilenameOrPath)[1]

    # preparing risk configurations for trades
    fileDictionary = qld_file.readDirectory(basePricingPath)
    riskConfss = []
    for dfTrades in dfTradesAggregated:
        for i in range(len(dfTrades)):
            dfTrade = dfTrades.iloc[i]
            for fileDFs in fileDictionary.values():
                headerTable = fileDFs[0]
                category = headerTable.loc[headerTable["Key"] == "Category"]["Value"].values[0]
                if category == "PriceRisk":
                    pricingSettings = headerTable.set_index("Key").loc[:, "Value"].to_dict()
                    riskConfss = generateRiskConfigurationssForTrade(fileDFs, marketDataFrameDictionary, dfTrade, pricingSettings)
            for riskConfs in riskConfss:
                # convert DataFrame to array only to avoid multiprecessing pickle mess :(
                argss.append([riskConfs, marketDataFrameDictionary, dfTrades.columns, dfTrade.values, pricingSettings, timestamp, outputPath])

    if doParallel:
        start_time = time.perf_counter()
        results = mp.Pool(mp.cpu_count()-1).starmap(computeTrade, argss)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logger.debug(f"elapsed time of parallel: {elapsed_time}")
    else:
        start_time = time.perf_counter()
        results = [computeTrade(*args) for args in argss]
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logger.debug(f"elapsed time of sequential: {elapsed_time}")

    filenames = [result["filename"] for result in results]
    filenames = list(dict.fromkeys(filenames))
    resultsReturn = {}
    resultsReturn["filenames"] = filenames
    logger.debug(resultsReturn)
    return resultsReturn, argss, timestamp
