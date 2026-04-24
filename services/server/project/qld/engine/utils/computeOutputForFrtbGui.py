import configparser
from project.qld.engine.utils.pricing import generalPricing
import outputForFrtbGui


def computeOutputForFrtbGui(iniFilename):
    config = configparser.ConfigParser()
    config.read(iniFilename)
    baseMarketPath = config["Default"]["baseMarketPath"]
    baseTradePath = config["Default"]["baseTradePath"]
    basePricingsPath = config["Default"]["basePricingsPath"]
    outputPath = config["Default"]["outputPath"]

    # tradeFilename = "swapTrades.xlsx"
    # tradeFilename = "fixedRateBonds.xlsx"
    # tradeFilenameFullPath = baseTradePath + "/" + tradeFilename
    tradeFilenameFullPath = baseTradePath

    result, argss, timestamp = generalPricing.computePriceRisk(tradeFilenameFullPath, baseMarketPath, basePricingsPath, outputPath, doParallel=True)
    outputForFrtbGui.exportFrtbGuiFile(tradeFilenameFullPath, baseMarketPath, result, timestamp, outputPath)
