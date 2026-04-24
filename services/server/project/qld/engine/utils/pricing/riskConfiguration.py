from enum import Enum
import QuantLib as ql
from copy import deepcopy
import json
import math

def parseCurrency(ccyStr):
    c = ccyStr.upper()
    if c == "USD":
        return ql.USDCurrency()
    elif c== "MYR":
        return ql.MYRCurrency()
    else:
        raise Exception("Unknown currency " + c)

class RiskType(Enum):
    def __str__(self):
        return self.name
    NPV = 0
    Delta = 1
    Gamma = 2
    Vega = 3
    Theta = 4
    Vanna = 5
    Volga = 6
    Rho = 7
    VegaRR = 8
    VegaBF = 9

class BumpType(Enum):
    def __str__(self):
        return self.name
    Absolute = 0
    Relative = 1
    
class BumpRate(Enum):
    def __str__(self):
        return self.name
    NA = 0
    Instrument = 1
    ZeroRate = 2

class BumpDetails:
    def __init__(self, jsonString):
        if jsonString != None and not (isinstance(jsonString, float) and math.isnan(jsonString)):
            d = json.loads(jsonString)
            self.bumpNode = d["bumpNodes"] if ("bumpNodes" in d) else None
            self.bumpRate = BumpRate[d["bumpRate"]] if ("bumpRate" in d) else BumpRate.NA
            self.zeroRateBumpTenors = d["zeroRateBumpTenors"] if ("zeroRateBumpTenors" in d) else None
            self.returnString = d["returnString"] if ("returnString" in d) else None

    bumpNodes = None
    bumpRate = BumpRate.NA
    zeroRateBumpTenors = None
    returnString = "None"
    def __str__(self):
        return self.returnString

class BumpObject:
    def __init__(self, bumpObjectName, position, bumpSize, bumpType, details = None):
        self.bumpObjectName = bumpObjectName
        self.position = position
        self.bumpSize = bumpSize
        self.bumpType = bumpType
        if details == None:
            self.details = BumpDetails()
        else:
            self.details = details

    def applyBump(self, baseValue):
        if isinstance(baseValue, ql.QuoteHandle):
            baseValue = baseValue.value()

        if self.bumpType == BumpType.Absolute:
            bumpedRate = baseValue + self.bumpSize
        elif self.bumpType == BumpType.Relative:
            bumpedRate = baseValue * (1.0 + self.bumpSize)

        if isinstance(baseValue, ql.QuoteHandle):
            bumpedRate = ql.QuoteHandle(ql.SimpleQuote(bumpedRate))
        return bumpedRate

class RiskConfiguration:
    def __init__(self, riskType, bumpObjects, multiplier):
        self.riskType = riskType
        self.bumpObjects = bumpObjects
        self.multiplier = multiplier

    def __str__(self):
        if self.bumpObjects:
            return str(self.riskType) + " " + self.bumpObjects.name + " " + str(self.bumpObjects.position)
        else:
            return str(self.riskType) + " None None"

#class RiskConfigurationRaw:
#    def __init__(self, riskType, bumpObjectsRaw):
#        self.riskType = riskType
#        self.bumpObjectsRaw = bumpObjectsRaw

#    def __str__(self):
#        return str(self.riskType) + " " + self.bumpObject.name + " " + str(self.bumpObject.position)

#def parseRiskConf(riskConfRaw):
#    riskConf = deepcopy(riskConfRaw)
#    for bumpObjectRaw in riskConfRaw.bumpObjectsRaw:
#        bumpObjectRaw = deepcopy(bumpObjectRaw)
#    currencyRaw = bumpObjectRaw.currency
#    currency = parseCurrency(currencyRaw)
#    riskConf.bumpObject.currency = currency
#    return riskConf

#def parseRiskConfs(riskConfsRaw):
#    riskConfs = [parseRiskConf(riskConfRaw) for riskConfRaw in riskConfsRaw]
#    return riskConfs

def parseRiskConf(riskConfRaw):
    riskConf = deepcopy(riskConfRaw)
    for bumpObjectRaw in riskConfRaw.bumpObjectsRaw:
        bumpObjectRaw = deepcopy(bumpObjectRaw)
    return riskConf

def parseRiskConfs(riskConfsRaw):
    riskConfs = [parseRiskConf(riskConfRaw) for riskConfRaw in riskConfsRaw]
    return riskConfs
