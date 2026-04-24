import matplotlib.pyplot as plt

import pandas as pd

from project.qld.engine.qld.QLD import ql
from project.qld.engine.qld import QLD
from project.qld.engine.utils.market import marketTools
from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.trade.ir.callable_floating_rate_bond import CallableFloatingRateBond


def source():
    baseMarketpath = "project/data/db/CallableFloatingRateBond"
    mktRaw = marketTools.loadMarketDataFrameDirectory(baseMarketpath)
    mktDic = marketTools.parseMarketDataFrameDictionary(mktRaw, None)

    evalDate = du.pythonDateTime2QLDDate(mktDic['Date'])
    ql.Settings.instance().evaluationDate = evalDate
    QLD.Settings.instance().evaluationDate = evalDate

    cal = ql.JointCalendar(ql.UnitedStates(ql.UnitedStates.Settlement), ql.UnitedKingdom())
    bdc = ql.Following
    dc = ql.Actual365Fixed()

    # yc_d = mktDic["USD.SOFR.CSA_USD"]
    yc_d = mktDic["USD.CREDIT.FUNDING"]
    yc_f = mktDic["USD.SOFR.CSA_USD"]  # forecast curve
    volMatrix = mktDic["USD.SOFR.VOLMATRIX"]

    # trade
    optionTenors = [ql.Period("2Y"), ql.Period("3Y"), ql.Period("4Y")]
    bondTenor = ql.Period("5Y")   # BondTenor -5Y

    startDate = ql.Date(12, ql.April, 2024)
    # print(startDate)
    endDate = cal.advance(startDate, bondTenor)
    oi = ql.Sofr(yc_f)

    # Source is Fed New YORK
    # Market watch https://www.newyorkfed.org/markets/reference-rates/sofr
    us_calendar = ql.UnitedStates(ql.UnitedStates.FederalReserve)
    file_path = r'C:\local\ql_build\QLD\QLD-Python-Test\Historical_SOFR_Data.xlsx'
    df = pd.read_excel(file_path)
    df['Effective Date'] = pd.to_datetime(df['Effective Date'])
    dates = []
    rates = []
    for _, row in df.iterrows():
        date = ql.Date(row['Effective Date'].day, row['Effective Date'].month, row['Effective Date'].year)
        rate = row['Rate']
        dates.append(date)
        rates.append(rate)
        # oi.addFixing(date, rate)
    ts = ql.RealTimeSeries(dates, rates)
    im = QLD.IndexManager.instance()
    im.setHistory("SOFRON Actual/360", ts)

    schedule = ql.Schedule(startDate, endDate, ql.Period(1, ql.Years), cal, ql.Following, ql.Following, ql.DateGeneration.Forward, False)
    nCF = len(schedule) - 1
    notional = 300000000.
    # coupon = 0.0495
    gearing = 1.
    spread = 0.03
    # with notional exchange (but zero for floating leg, we express a bond notinal payment)
    nonCallBond = QLD.NonstandardGeneralSwap(ql.Swap.Receiver,  # pays floating rate (gearing and spread) and notional seen from bank side
                                             [0.] * nCF, [notional] * nCF,
                                             schedule, [0.] * nCF, ql.Thirty360(ql.Thirty360.BondBasis), 0,
                                             schedule, oi, [gearing] * nCF, [spread] * nCF,  # floatingNormina with gearing and spread
                                             ql.Thirty360(ql.Thirty360.BondBasis), 0, False, True)

    # pricing of swap
    engine = ql.DiscountingSwapEngine(yc_d)
    nonCallBond.setPricingEngine(engine)
    npvAsNonstardardGeneralSwap = nonCallBond.NPV()
    npvAsNonstardardGeneralSwap1 = nonCallBond.legNPV(0)
    npvAsNonstardardGeneralSwap2 = nonCallBond.legNPV(1)
    print("Non-call bond as NonstandardGeneralSwap: " + str(npvAsNonstardardGeneralSwap))
    print("Non-call bond as NonstandardGeneralSwap 1st leg: " + str(npvAsNonstardardGeneralSwap1))
    print("Non-call bond as NonstandardGeneralSwap 2nd leg: " + str(npvAsNonstardardGeneralSwap2))

    # exercise
    decisionLag = 10
    callDates = [cal.advance(startDate, optionTenor) for optionTenor in optionTenors]
    # scheduleCall = ql.Schedule(callDate, endDate, ql.Period(1, ql.Years), cal, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)
    # with notional exchange (but zero for floating leg, we express a bond)
    callSwap = QLD.NonstandardGeneralSwap(ql.Swap.Payer, [0.] * nCF, [notional] * nCF,
                                          schedule, [0.] * nCF, ql.Thirty360(ql.Thirty360.BondBasis), 0,
                                          schedule, oi, [gearing] * nCF, [spread] * nCF,
                                          ql.Thirty360(ql.Thirty360.BondBasis), 0, False, True)
    decisionLag = 10
    execDates = [cal.advance(callDate, -decisionLag, ql.Days) for callDate in callDates]
    exercise = ql.BermudanExercise(execDates)
    nCFCall = len(callDates)  # - 1
    rebatedExercise = ql.RebatedExercise(exercise, [-notional] * nCFCall, decisionLag, cal)  # adding initial notional payment
    callSwaption = QLD.NonstandardGeneralSwaption(callSwap, rebatedExercise)

    # model
    initSigma = 0.01
    initKappa = 0.02
    gsr = ql.Gsr(yc_f, execDates[:-1], [ql.QuoteHandle(ql.SimpleQuote(initSigma))] * (nCFCall), [ql.QuoteHandle(ql.SimpleQuote(initKappa))] * (nCFCall))
    nbPoints = 64
    nbStd = 7
    swaptionEngine = ql.Gaussian1dSwaptionEngine(gsr, nbPoints, nbStd, True, False, yc_d)
    method = ql.LevenbergMarquardt()
    ec = ql.EndCriteria(1000, 10, 1.e-8, 1.e-8, 1.e-8)

    # calibration - ATM swaption
    nonstandardSwaptionEngine = QLD.Gaussian1dNonstandardGeneralSwaptionEngine(gsr, nbPoints, nbStd, True, False, ql.QuoteHandle(), yc_d)
    callSwaption.setPricingEngine(nonstandardSwaptionEngine)
    swap_index = ql.OvernightIndexedSwapIndex("SOFR", bondTenor, 0, ql.USDCurrency(), oi)
    swap_index = swap_index.clone(yc_f, yc_d)
    curve = swap_index.discountingTermStructure()
    basket = callSwaption.calibrationBasket(swap_index, volMatrix.currentLink(), QLD.GeneralBasketGeneratingEngine.Naive)
    print(basket)
    for basket_i in basket:
        ql.as_black_helper(basket_i).setPricingEngine(swaptionEngine)
        basket_i.setPricingEngine(swaptionEngine)
    gsr.calibrateVolatilitiesIterative(basket, method, ec)
    print(basket, gsr.volatility())

    # pricing of swaption
    npvAsNonstandardGeneralSwaption = callSwaption.NPV()
    print("Callability As NonstandardGeneralSwaption: " + str(npvAsNonstandardGeneralSwaption))
    print("Callable bond: " + str(npvAsNonstardardGeneralSwap + npvAsNonstandardGeneralSwaption))


def test1():
    """Basic test of CallableFloatingRateBond pricing"""
    #####################################
    ###          INPUT                ###
    #####################################
    evaluation_date = "2024-12-31"
    currency = "USD"
    notional = 300000000.0
    start_date = "2024-04-12"
    bond_tenor = "5Y"
    calendar = ["US"]
    day_count_convention = "30/360"
    business_day_convention = "Following"
    option_tenors = ["2Y", "3Y", "4Y"]
    exercise_lag = 10
    spread = 0.03
    gearing = 1.0
    discount_curve_name = 'USD.CREDIT.FUNDING'
    forecast_curve_name = 'USD.SOFR.CSA_USD'
    vol_matrix = 'USD.SOFR.VOLMATRIX'

    #####################################
    ###          TRADE                ###
    #####################################
    test_bond = CallableFloatingRateBond(
        evaluation_date=evaluation_date,
        currency=currency,
        notional=notional,
        start_date=start_date,
        bond_tenor=bond_tenor,
        calendar=calendar,
        day_count_convention=day_count_convention,
        business_day_convention=business_day_convention,
        option_tenors=option_tenors,
        exercise_lag=exercise_lag,
        spread=spread,
        gearing=gearing,
        discount_curve_name=discount_curve_name,
        forecast_curve_name=forecast_curve_name,
        vol_matrix=vol_matrix
    )

    test_bond.price()
    print(f"Callable Floating Rate Bond Results: {test_bond.result}")

    return test_bond


def test2():
    trade_data = {
        'evaluation_date': '2024-12-31',
        'currency': 'USD',
        'notional': 100000000,
        'start_date': '2024-04-12',
        'bond_tenor': '5Y',
        'calendar': ['US'],
        'day_count_convention': '30/360',
        'business_day_convention': 'Following',
        'option_tenors': ['2Y', '3Y', '4Y'],
        'exercise_lag': 20,
        'discount_curve_name': 'USD.CREDIT.FUNDING',
        'forecast_curve_name': 'USD.SOFR.CSA_USD',
        'vol_matrix': 'USD.SOFR.VOLMATRIX',
        'spread': 0.03, 'gearing': 1,
        'risk_curve_name': 'USD.CREDIT.FUNDING',
        'bump_type': 'Absolute',
        'bump_points': '1,5,10,20,30,50'
    }

    trade = CallableFloatingRateBond(
        evaluation_date=trade_data.get('evaluation_date'),
        currency=trade_data.get('currency'),
        notional=trade_data.get('notional'),
        start_date=trade_data.get('start_date'),
        bond_tenor=trade_data.get('bond_tenor'),
        calendar=trade_data.get('calendar'),
        day_count_convention=trade_data.get('day_count_convention'),
        business_day_convention=trade_data.get('business_day_convention'),
        option_tenors=trade_data.get('option_tenors'),
        exercise_lag=trade_data.get('exercise_lag'),
        discount_curve_name=trade_data.get('discount_curve_name'),
        forecast_curve_name=trade_data.get('forecast_curve_name'),
        vol_matrix=trade_data.get('vol_matrix'),
        spread=trade_data.get('spread'),
        gearing=trade_data.get('gearing', 1.0)
    )

    bump_points = trade_data.get('bump_points', None)
    curve_name = trade_data.get('risk_curve_name', None)
    bump_type = trade_data.get('bump_type')
    risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
                                                    curve_name=curve_name,
                                                    bump_type=bump_type)
    risk_sensitivity = {
        'BP': [0] + risk_results['bump_points'],
        'NPV': [risk_results['base_npv']] + risk_results['npv_values']
    }
    result = {
        'npv': risk_results['base_npv'],
        'risk_sensitivity': risk_sensitivity
    }

    print(result)


def test_risk_sensitivity():
    """Test risk sensitivity calculation for CallableFloatingRateBond"""
    evaluation_date = "2024-12-31"
    currency = "USD"
    notional = 300000000.0
    start_date = "2024-04-12"
    bond_tenor = "5Y"
    calendar = ["US"]
    day_count_convention = "30/360"
    business_day_convention = "Following"
    option_tenors = ["2Y", "3Y", "4Y"]
    exercise_lag = 10
    spread = 0.03
    gearing = 1.0
    discount_curve_name = 'USD.CREDIT.FUNDING'
    forecast_curve_name = 'USD.SOFR.CSA_USD'
    vol_matrix = 'USD.SOFR.VOLMATRIX'

    trade = CallableFloatingRateBond(
        evaluation_date=evaluation_date,
        currency=currency,
        notional=notional,
        start_date=start_date,
        bond_tenor=bond_tenor,
        calendar=calendar,
        day_count_convention=day_count_convention,
        business_day_convention=business_day_convention,
        option_tenors=option_tenors,
        exercise_lag=exercise_lag,
        spread=spread,
        gearing=gearing,
        discount_curve_name=discount_curve_name,
        forecast_curve_name=forecast_curve_name,
        vol_matrix=vol_matrix
    )

    # Use the risk sensitivity methods
    bump_points = [1, 5, 10, 15, 20, 25, 30, 50]

    # Test discount curve sensitivity
    discount_risk_results = trade.calculate_risk_sensitivity(
        bump_points=bump_points,
        curve_name=discount_curve_name
    )

    # Test forecast curve sensitivity
    forecast_risk_results = trade.calculate_risk_sensitivity(
        bump_points=bump_points,
        curve_name=forecast_curve_name
    )

    # Prepare data for plotting discount curve sensitivity
    discount_risk_dict = {
        'BP': [0] + discount_risk_results['bump_points'],
        'NPV': [discount_risk_results['base_npv']] + discount_risk_results['npv_values']
    }

    # Prepare data for plotting forecast curve sensitivity
    forecast_risk_dict = {
        'BP': [0] + forecast_risk_results['bump_points'],
        'NPV': [forecast_risk_results['base_npv']] + forecast_risk_results['npv_values']
    }

    # Create subplots for both sensitivities
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Discount curve sensitivity
    ax1.plot(discount_risk_dict['BP'], discount_risk_dict['NPV'], marker='o')
    ax1.set_xlabel('Basis points')
    ax1.set_ylabel('NPV')
    ax1.set_title('Discount Curve Risk Sensitivity (USD.CREDIT.FUNDING)')
    ax1.grid(True)

    # Forecast curve sensitivity
    ax2.plot(forecast_risk_dict['BP'], forecast_risk_dict['NPV'], marker='o')
    ax2.set_xlabel('Basis points')
    ax2.set_ylabel('NPV')
    ax2.set_title('Forecast Curve Risk Sensitivity (USD.SOFR.CSA_USD)')
    ax2.grid(True)

    plt.tight_layout()
    plt.show()

    print("Discount Curve Risk Results:")
    print(f"Base NPV: {discount_risk_results['base_npv']}")
    print(f"DV01 estimates: {discount_risk_results['dv01_estimates']}")

    print("\nForecast Curve Risk Results:")
    print(f"Base NPV: {forecast_risk_results['base_npv']}")
    print(f"DV01 estimates: {forecast_risk_results['dv01_estimates']}")


if __name__ == "__main__":
    print("=== Test 1: Basic Pricing ===")
    test2()

    # print("\n=== Test 5: Risk Sensitivity ===")
    # test_risk_sensitivity()
