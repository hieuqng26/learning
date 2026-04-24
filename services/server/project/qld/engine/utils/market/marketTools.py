from copy import deepcopy
from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql
from project.qld.engine.utils.pricing.riskConfiguration import BumpObject
from project.qld.engine.utils.tools import qld_file
from project.qld.engine.utils.market import parseUtils
from project.qld.engine.utils.market.IR import ir_market
from project.qld.engine.utils.market.FX import fx_market
from project.qld.engine.utils.market.EQ import eq_market


def loadMarketDataFrameDirectory(baseMarketPath):
    dc = {}
    fileDictionary = qld_file.readDirectory(baseMarketPath)
    for filename, fileDFs in fileDictionary.items():
        headerTable = fileDFs[0]
        headerTable.loc[len(headerTable)] = ["filename", filename]
        # headerTable.append({"Key": "filename", "Value": filename}, ignore_index=True)
        category = headerTable.loc[headerTable["Key"] == "Category"]["Value"].values[0]
        if category == "Market":
            date = headerTable.loc[headerTable["Key"] == "Date"]["Value"].values[0]
            name = headerTable.loc[headerTable["Key"] == "Name"]["Value"].values[0]
            if "Date" in dc:
                if dc["Date"] != date:
                    raise ValueError("Date " + str(date) + " of " + name + " is not the same as market date of other market objects: " + str(dc["Date"]))
            else:
                dc["Date"] = date
            if name in dc:
                raise ValueError("Market " + name + " already exists")
            dc[name] = fileDFs
            # pricingSettings = headerTable.set_index("Key").loc[:,"Value"].to_dict()
    return dc

# dc = loadMarketDataFrameDirectory("../QLD-Python-Test/P202301/input")
# print(dc)


def parseMarketDataFrameDictionary(marketDataFrameDictionaryRaw, riskConf):
    dc = {}
    for name, dfs in marketDataFrameDictionaryRaw.items():
        if name == "Date":
            dc['Date'] = dfs
        else:
            headerTable = dfs[0]
            marketDataType = headerTable.loc[headerTable["Key"] == "Type"]["Value"].values[0]
            if marketDataType == "EvaluationDate":
                parsedObject = parseUtils.parseEvaluationDate(dfs, riskConf)
                dc[name] = parsedObject
            if marketDataType == "YieldCurve":
                parsedObject = ir_market.parseYieldCurve(dfs, riskConf, marketDataFrameDictionaryRaw)
                dc[name] = parsedObject
            if marketDataType == "IRVol":
                parsedObject = ir_market.parseIRVol(dfs, riskConf, marketDataFrameDictionaryRaw)
                dc[name] = parsedObject
            if marketDataType == "FXSpot":
                parsedObject = fx_market.parseFXSpot(dfs, riskConf)
                dc[name] = parsedObject
            if marketDataType == "FXVol":
                parsedObject, fxSpot = fx_market.parseFXVol(dfs, riskConf, marketDataFrameDictionaryRaw)
                dc[name] = (parsedObject, fxSpot)
            if marketDataType == "EQSpot":
                parsedObject = eq_market.parseEQSpot(dfs, riskConf)
                dc[name] = parsedObject
            if marketDataType == "EQDividend":
                parsedObject = eq_market.parseEQDividend(dfs, riskConf, marketDataFrameDictionaryRaw)
                dc[name] = parsedObject
            if marketDataType == "EQVol":
                parsedObject, eqSpot = eq_market.parseEQVol(dfs, riskConf, marketDataFrameDictionaryRaw)
                dc[name] = (parsedObject, eqSpot)

    return dc


def isRelevantBumpObjectToTradeMarketObject(bumpObjectName, tradeMarketObjectName, marketDataFrameDictionary):
    if bumpObjectName == tradeMarketObjectName:
        return True
    elif tradeMarketObjectName in marketDataFrameDictionary:
        headerTable = marketDataFrameDictionary[tradeMarketObjectName][0]
        baseDiscountingCurveNameRow = headerTable.loc[headerTable["Key"] == "BaseDiscountingCurve"]["Value"]
        if len(baseDiscountingCurveNameRow):
            baseDiscountingCurveName = baseDiscountingCurveNameRow.values[0]
            return isRelevantBumpObjectToTradeMarketObject(bumpObjectName, baseDiscountingCurveName, marketDataFrameDictionary)
    return False

# dcRaw = loadMarketDataFrameDirectory("../QLD-Python-Test/P202301/pricingInput")
# print(dcRaw)
# riskConf = riskconf.RiskConfiguration(riskconf.RiskType.NPV, None, 1.)
# dc = parseMarketDataFrameDictionary(dcRaw, riskConf)
# print(dc)
