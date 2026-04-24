from project.qld.engine.utils.foundation.convention import currency
from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.market import parseUtils
from project.qld.engine.utils.market.IR.ir_market import Sora
import pandas as pd
from project.qld.engine.qld.QLD import ql


def getIRIborIndexFromName(currency, tenor, forecastCurve=None):
    if currency == ql.USDCurrency():
        tenor = ql.Period("3M") if tenor == None else tenor
        if forecastCurve == None:
            return ql.USDLibor(tenor)
        else:
            return ql.USDLibor(tenor, forecastCurve)
    elif currency == ql.MYRCurrency():
        tenor = ql.Period("3M") if tenor == None else tenor
        if forecastCurve == None:
            return ql.Libor("KLibor", tenor, 0, ql.MYRCurrency(),
                            KualaLumpur(),
                            ql.Actual365Fixed())
        else:
            return ql.Libor("KLibor", tenor, 0, ql.MYRCurrency(),
                            KualaLumpur(),
                            ql.Actual365Fixed(), forecastCurve)


def getIROisIndexFromName(currency, forecastCurve=None):
    if currency == ql.USDCurrency():
        if forecastCurve == None:
            return ql.Sofr()
        else:
            return ql.Sofr(forecastCurve)
    elif currency == ql.GBPCurrency():
        if forecastCurve == None:
            return ql.Sonia()
        else:
            return ql.Sonia(forecastCurve)
    elif currency == ql.SGDCurrency():
        if forecastCurve == None:
            return Sora()
        else:
            return Sora(forecastCurve)
    else:
        raise ("Unkown OIS SWAP for currency:" + currency.code())


def iborSwap(notional_ccy, notional, typeStr, start_date, end_date, calendarStr, business_day_convention, fixing_lag, fixed_rate, fixed_frequency, fixed_day_count,
             float_index, float_spread, float_frequency, float_day_count, discounting, marketDataDictionary):
    ccyStr, _, tenorStr = float_index.split(".")
    ccy = currency.getCurrency(ccyStr)
    forecast_curve = marketDataDictionary[float_index]
    index = getIRIborIndexFromName(ccy, ql.Period(tenorStr), forecast_curve)

    if ccy == ql.USDCurrency():  # temporary code for fixing
        # Source is Bloomberg otherwise stated
        # Market watch https://www.marketwatch.com/investing/interestrate/liborusd3m?countrycode=mr
        index.addFixing(ql.Date(31, 3, 2022), 0.96157 / 100.0)
    start_date = du.pythonDateTime2QLDDate(start_date)
    end_date = du.pythonDateTime2QLDDate(end_date)
    # build a swap trade
    calendar = parseUtils.parseCalendar(calendarStr)
    fixedTenor = ql.Period(fixed_frequency)
    floatTenor = ql.Period(float_frequency)
    bdc = parseUtils.parseBusinessDayConvention(business_day_convention)
    fixed_schedule = ql.Schedule(start_date, end_date, fixedTenor, calendar, bdc, bdc, ql.DateGeneration.Forward, False)
    float_schedule = ql.Schedule(start_date, end_date, floatTenor, calendar, bdc, bdc, ql.DateGeneration.Forward, False)

    fixed_leg_daycount = parseUtils.parseDayCount(fixed_day_count)
    float_leg_daycount = parseUtils.parseDayCount(float_day_count)

    if typeStr.upper() == "PAYER":
        swapType = ql.VanillaSwap.Payer
    elif typeStr.upper() == "RECEIVER":
        swapType = ql.VanillaSwap.Receiver
    else:
        raise ValueError("Unknown vanilla swap type: " + typeStr)
    return ql.VanillaSwap(swapType, notional, fixed_schedule, fixed_rate, fixed_leg_daycount, float_schedule, index, float_spread, float_leg_daycount)


def addOISFixing(ccy_str, ois_index, marketDataDictionary,
                 file_path='project/data/db/YIELDCURVE/Historical_SOFR_Data.xlsx'):
    ccy = currency.getCurrency(ccy_str)
    forecast_curve = marketDataDictionary[ois_index]
    index = getIROisIndexFromName(ccy, forecast_curve)

    if ccy == ql.USDCurrency():
        file_path = 'project/data/db/YIELDCURVE/Historical_SOFR_Data.xlsx'
    elif ccy == ql.SGDCurrency():
        file_path = 'project/data/db/YIELDCURVE/Historical_SORA_Data.xlsx'
    elif ccy == ql.GBPCurrency():
        file_path = 'project/data/db/YIELDCURVE/Historical_SONIA_Data.xlsx'
    else:
        raise ValueError("Unknown currency: " + ccy.code())

    # Add fixings
    # Source is Fed New YORK
    # Market watch https://www.newyorkfed.org/markets/reference-rates/sofr
    df = pd.read_excel(file_path)
    df['Effective Date'] = pd.to_datetime(df['Effective Date'])
    for _, row in df.iterrows():
        date = ql.Date(row['Effective Date'].day, row['Effective Date'].month, row['Effective Date'].year)
        rate = row['Rate']
        index.addFixing(date, rate)
    return index


def oiSwap(notional_ccy, notional, typeStr, start_date, end_date, payment_lag, calendarStr, business_day_convention, fixed_rate, fixed_frequency, fixed_day_count,
           ois_index, ois_spread, discounting, marketDataDictionary):

    ccyStr = notional_ccy
    ccy = currency.getCurrency(ccyStr)
    index = addOISFixing(notional_ccy, ois_index, marketDataDictionary)

    start_date = du.pythonDateTime2QLDDate(start_date)
    end_date = du.pythonDateTime2QLDDate(end_date)
    calendar = parseUtils.parseCalendar(calendarStr)
    fixedTenor = ql.Period(fixed_frequency)
    bdc = parseUtils.parseBusinessDayConvention(business_day_convention)
    schedule = ql.Schedule(start_date, end_date, fixedTenor, calendar, bdc, bdc, ql.DateGeneration.Forward, False)
    fixed_leg_daycount = parseUtils.parseDayCount(fixed_day_count)
    if typeStr.upper() == 'PAYER':
        swapType = ql.OvernightIndexedSwap.Payer
    elif typeStr.upper() == 'RECEIVER':
        swapType = ql.OvernightIndexedSwap.Receiver
    else:
        raise ValueError("Unknown ois swap type: " + typeStr)

    return ql.OvernightIndexedSwap(swapType, notional, schedule, fixed_rate, fixed_leg_daycount, index, ois_spread, int(payment_lag))


def parseIRSwap(dfTrade, marketDataDictionary):
    trade = iborSwap(dfTrade.NotionalCurrency, float(dfTrade.Notional), dfTrade.Type, dfTrade.StartDate, dfTrade.EndDateOrTenor, dfTrade.Calendar,
                     dfTrade.BusinessDayConvention, dfTrade.FixingLag,
                     dfTrade.FixedRate, dfTrade.FixedFrequency, dfTrade.FixedDayCount,
                     dfTrade.FloatIndex, dfTrade.FloatSpread, dfTrade.FloatFrequency, dfTrade.FloatDayCount,
                     dfTrade.Discounting, marketDataDictionary)
    return trade


def parseIROISwap(dfTrade, marketDataDictionary):

    trade = oiSwap(dfTrade.NotionalCurrency, float(dfTrade.Notional), dfTrade.Type, dfTrade.StartDate, dfTrade.EndDateOrTenor, dfTrade.PaymentLag,
                   dfTrade.Calendar,
                   dfTrade.BusinessDayConvention,
                   dfTrade.FixedRate, dfTrade.FixedFrequency, dfTrade.FixedDayCount,
                   dfTrade.OvernightIndex, dfTrade.OvernightSpread,
                   dfTrade.Discounting, marketDataDictionary)
    return trade


def parseIRFixedRateBond(dfTrade):
    settlementLag = int(dfTrade.SettlementLag)
    calendar = parseUtils.parseCalendar(dfTrade.Calendar)
    startDate = du.pythonDateTime2QLDDate(dfTrade.StartDate)
    endDate = du.pythonDateTime2QLDDate(dfTrade.EndDateOrTenor)
    notional = float(dfTrade.Notional)
    fixedFreq = ql.Period(dfTrade.FixedFrequency)
    fixedRate = float(dfTrade.FixedRate)
    dc = parseUtils.parseDayCount(dfTrade.DayCount)
    bdc = parseUtils.parseBusinessDayConvention(dfTrade.BusinessDayConvention)
    trade = ql.FixedRateBond(settlementLag, calendar, notional, startDate, endDate, fixedFreq, [fixedRate], dc, bdc)
    return trade


def parseIRFloatingRateBond(dfTrade, marketDataDictionary):
    notional_ccy = dfTrade.NotionalCurrency
    settlementLag = int(dfTrade.SettlementLag)
    calendar = parseUtils.parseCalendar(dfTrade.Calendar)
    startDate = du.pythonDateTime2QLDDate(dfTrade.StartDate)
    endDate = du.pythonDateTime2QLDDate(dfTrade.EndDateOrTenor)
    notional = float(dfTrade.Notional)
    freq = ql.Period(dfTrade.FixedFrequency)
    dc = parseUtils.parseDayCount(dfTrade.DayCount)
    bdc = parseUtils.parseBusinessDayConvention(dfTrade.BusinessDayConvention)
    ois_index = dfTrade.Discounting
    index = addOISFixing(notional_ccy, ois_index, marketDataDictionary)
    schedule = ql.Schedule(startDate, endDate, freq, calendar, bdc, bdc, ql.DateGeneration.Forward, False)
    # fixingDays = 0
    # gearings = [1.0]
    # spreads = [0.0]
    trade = ql.FloatingRateBond(settlementLag, notional, schedule, index, dc, bdc, spreads=spreads)
    # fixingDays, gearings, spreads
    return trade
