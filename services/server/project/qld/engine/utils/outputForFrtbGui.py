from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql
import pandas as pd
from project.qld.engine.utils.pricing import riskConfiguration as riskconf
from project.qld.engine.utils.trade import generalTrade
from project.qld.engine.utils.market import marketTools
from project.qld.engine.utils.foundation.date import date_utils as du
import os


def exportFrtbGuiFile(tradeFilenameFullPath, baseMarketPath, result, timestamp, outputPath):
    marketDataFrameDictionary = marketTools.loadMarketDataFrameDirectory(baseMarketPath)

    dfInputTrades = pd.DataFrame(columns=["TradeID", "Product", "IsOptional", "Exotic Underlying", "IsLinear",
                                 "Notional", "SimPV", "LGD", "CptyRating", "CptyType", "Cpty", "Sector", "CreditQuality"])
    dfInputSensitivities = pd.DataFrame(columns=["Factor", "ValueType", "Value"])

    dfTradesAggregated = generalTrade.loadTradesDataFrames(tradeFilenameFullPath)[1]
    # trades = None
    for dfTrades in dfTradesAggregated:
        trades = dfTrades[["TradeID", "TradeType", "Notional"]]
        tradeFileNameNoExtension = os.path.splitext(dfTrades.filename[0])[0]
        # if not isinstance(trades, pd.DataFrame):
        #    trades = dfTrades[["TradeID", "TradeType", "Notional"]]
        # else:
        #    trades.append(dfTrades[["TradeID", "TradeType", "Notional"]])

        # load result files
        for resultFilename in result["filenames"]:
            resultFilenameWithoutPath = os.path.basename(resultFilename)
            if resultFilenameWithoutPath.startswith(tradeFileNameNoExtension):
                dfResult = pd.read_csv(resultFilename, skipinitialspace=True)
                riskType = riskconf.RiskType[dfResult["riskType"][0]]

                tradeIDs = trades["TradeID"]
                tradeTypes = trades["TradeType"].replace(to_replace={
                    "IRSwap": "IR Swap",
                    "IRFixedRateBond": "IR Fixed Rate Bond",
                    "FXForward": "FX Forward",
                    "FXSpot": "FX Spot"})
                isOptionals = trades["TradeType"].replace(to_replace={
                    "IRSwap": False,
                    "IRFixedRateBond": False,
                    "FXForward": False,
                    "FXSpot": False})
                exoticUnderlyings = trades["TradeType"].replace(to_replace={
                    "IRSwap": False,
                    "IRFixedRateBond": False,
                    "FXForward": False,
                    "FXSpot": False})
                isLinears = trades["TradeType"].replace(to_replace={
                    "IRSwap": True,
                    "IRFixedRateBond": False,
                    "FXForward": True,
                    "FXSpot": True})
                LGDs = [0.4] * len(trades)
                # details = dfResult.set_index("tradeID").loc[tradeIDs]["details"]
                emptyList = [None] * len(trades)
                cptyTypes = ["Corporate"] * len(trades)
                if riskType == riskconf.RiskType.NPV:
                    notionals = trades["Notional"]
                    NPVs = dfResult.set_index("tradeID").loc[tradeIDs]["value"]
                    for j in range(len(tradeIDs)):
                        dfInputTrades.loc[len(
                            dfInputTrades)] = tradeIDs[j], tradeTypes[j], isOptionals[j], exoticUnderlyings[j], isLinears[j], notionals[j], NPVs[j], LGDs[j], emptyList[j], cptyTypes[j], emptyList[j], emptyList[j], emptyList[j]
                else:
                    for j in range(len(dfResult)):
                        riskType = riskconf.RiskType[dfResult["riskType"][j]]
                        riskBumpObjectName = dfResult["riskBumpObjectNames"][j]
                        dfBumpObjectHeaderTable = marketDataFrameDictionary[riskBumpObjectName][0]
                        bumpMarketObjectType = dfBumpObjectHeaderTable.loc[dfBumpObjectHeaderTable["Key"] == "Type"]["Value"].values[0]
                        bumpPosition = dfResult["riskBumpPositions"][j]
                        bumpDetails = dfResult["details"][j]
                        value = dfResult["value"][j]
                        if riskType == riskconf.RiskType.Delta:
                            if bumpMarketObjectType == "YieldCurve":
                                riskBumpObjectNameSplit = riskBumpObjectName.split(".")
                                bumpCurrency = riskBumpObjectNameSplit[0]
                                yieldCurveSubName = riskBumpObjectNameSplit[1]
                                if bumpPosition >= 0:
                                    riskBumpObjectNameSplit = riskBumpObjectName.split(".")
                                    bumpCurrency = riskBumpObjectNameSplit[0]
                                    yieldCurveSubName = riskBumpObjectNameSplit[1]
                                    if yieldCurveSubName.upper() != "CREDIT":
                                        # Delta GIRR
                                        tenorInYear = du.simpleYearFraction(ql.Period(bumpDetails))
                                        factor = dfResult["tradeID"][j] + "." + str(riskType) + "|GIRR|" + bumpCurrency + "|" + f'{tenorInYear:g}' + " year"
                                        valueType = "Sensitivity (PV)"
                                    else:
                                        # Delta CSR
                                        tenorInYear = du.simpleYearFraction(ql.Period(bumpDetails))
                                        factor = dfResult["tradeID"][j] + "." + str(riskType) + "|CSR|" + bumpCurrency + "|" + f'{tenorInYear:g}' + " year"
                                        valueType = "Sensitivity (PV)"
                                else:
                                    if yieldCurveSubName.upper() != "CREDIT":
                                        # Curvature GIRR
                                        factor = dfResult["tradeID"][j] + ".Curvature" + "|GIRR|" + bumpCurrency + "|"
                                        bumpSize = bumpDetails if isinstance(bumpDetails, float) else float(bumpDetails.split()[-1])
                                        valueType = "NPV+" if bumpSize > 0 else "NPV-"
                                    else:
                                        # Curvature CSR
                                        factor = dfResult["tradeID"][j] + ".Curvature" + "|CSR|" + bumpCurrency + "|"
                                        bumpSize = bumpDetails if isinstance(bumpDetails, float) else float(bumpDetails.split()[-1])
                                        valueType = "NPV+" if bumpSize > 0 else "NPV-"
                            elif bumpMarketObjectType == "FXSpot":
                                # Delta FX
                                fxPair = riskBumpObjectName
                                fxPairWithSlash = fxPair[:3] + "/" + fxPair[3:]
                                factor = dfResult["tradeID"][j] + "." + str(riskType) + "|FX|" + fxPairWithSlash + "|"
                                valueType = "Sensitivity (PV)"
                        elif riskType == riskconf.RiskType.Vega:
                            raise NotImplementedError("Not implemented")
                        else:
                            raise ValueError("Unknow risk type: " + str(riskType))
                        dfInputSensitivities.loc[len(dfInputSensitivities)] = factor, valueType, value

    outputfilename = outputPath + "/" + "input_data_" + timestamp + ".xlsx"
    with pd.ExcelWriter(outputfilename) as writer:
        dfInputTrades.to_excel(writer, "input_trades", index=False)
        dfInputSensitivities.to_excel(writer, "input_sensitivities", index=False)
