from copy import deepcopy
import os
from project.qld.engine.utils.tools import qld_file
from project.qld.engine.utils.trade.IR import ir_trades
from project.qld.engine.utils.trade.FX import fx_trades


def loadTradesDataFrames(fullPathFilenameOrPath):
    fileDataFrameDictionary = {}
    if os.path.isdir(fullPathFilenameOrPath):
        directory = fullPathFilenameOrPath
        fileDataFrameDictionary = qld_file.readDirectory(fullPathFilenameOrPath)
    else:
        filename = os.path.basename(fullPathFilenameOrPath)
        directory = os.path.dirname(fullPathFilenameOrPath)
        fileDataFrameDictionary[filename] = qld_file.readData(fullPathFilenameOrPath)

    dfsTradesFilteredAggregated = []
    for filename, dfs in fileDataFrameDictionary.items():
        headerTable = dfs[0]
        category = headerTable.loc[headerTable["Key"] == "Category"]["Value"].values[0]
        if category == "Trade":
            dfsTradesFiltered = deepcopy(dfs[1][dfs[1].Calculate == True])
            dfsTradesFiltered.insert(0, "directory", [directory] * len(dfsTradesFiltered))
            dfsTradesFiltered.insert(1, "filename", [filename] * len(dfsTradesFiltered))

            if not dfsTradesFilteredAggregated:  # only if dfsTradesFiltered, add a header table
                dfsTradesFilteredAggregated.append(headerTable)
                dfsTradesFilteredAggregated.append([dfsTradesFiltered])
            else:
                dfsTradesFilteredAggregated[1].append(dfsTradesFiltered)

    return dfsTradesFilteredAggregated


def parseTrades(dfTrades, marketDataDictionary):
    trades = []
    for i in range(len(dfTrades)):
        dfTrade = dfTrades.iloc[i]
        tradeType = dfTrade.TradeType
        if tradeType == "IRSwap":
            trade = ir_trades.parseIRSwap(dfTrade, marketDataDictionary)
        elif tradeType == "IROISwap":
            trade = ir_trades.parseIROISwap(dfTrade, marketDataDictionary)
        elif tradeType == "IRFixedRateBond":
            trade = ir_trades.parseIRFixedRateBond(dfTrade)
        elif tradeType == "IRFloatingRateBond":
            trade = ir_trades.parseIRFloatingRateBond(dfTrade, marketDataDictionary)
        elif tradeType == "FXForward":
            trade = fx_trades.parseFXForward(dfTrade)
        elif tradeType == "FXSpot":
            trade = fx_trades.parseFXSpot(dfTrade)
        elif tradeType == "FXVanillaOption":
            trade = fx_trades.parseFXVanillaOption(dfTrade)
        else:
            raise ValueError("Unknown trade type: " + tradeType)
        trades.append(trade)

    return trades

# forecastCurve =ql.YieldTermStructureHandle(ql.FlatForward(ql.Date(1, 1, 2023), 0.02, ql.Actual365Fixed()))
# curveName = "USD.LIBOR.3M"
# marketDataDictionary = {}
# marketDataDictionary[curveName] = forecastCurve
# filename = "../QLD-Python-Test/P202301/pricingInput/swapTrades.xlsx"
# trades = loadTrades(filename, marketDataDictionary)
# print(trades)
