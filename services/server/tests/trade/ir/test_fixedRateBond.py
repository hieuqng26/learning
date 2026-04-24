import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from project.qld.engine.qld import QLD
from project.qld.engine.qld.QLD import ql
from project.qld.engine.utils.pricing import generalPricing
from project.qld.engine.utils.market import marketTools
from project.qld.engine.utils.pricing import riskConfiguration as riskconf
from project.qld.engine.utils.foundation.date import date_utils as du
from project.qld.engine.utils.market import parseUtils
from project.qld.trade.ir.ir_fixed_rate_bond import IRFixedRateBond


def test1():
    baseMarketPath = "project/data/db/IRFixedRateBond"

    def parseTrades(trade_input):
        settlementLag = int(trade_input.settlement_lag)
        calendar = parseUtils.parseCalendar(trade_input.calendar)
        startDate = du.pythonDateTime2QLDDate(trade_input.start_date)
        endDate = du.pythonDateTime2QLDDate(trade_input.end_date)
        notional = float(trade_input.notional)
        fixedFreq = ql.Period(trade_input.fixed_frequency)
        fixedRate = float(trade_input.fixed_rate)
        dc = parseUtils.parseDayCount(trade_input.day_count_convention)
        bdc = parseUtils.parseBusinessDayConvention(trade_input.business_day_convention)
        trade = ql.FixedRateBond(settlementLag, calendar, notional, startDate, endDate, fixedFreq, [fixedRate], dc, bdc)
        return trade

    trade_input = IRFixedRateBond(
        evaluation_date=datetime(2024, 12, 31),
        currency='PLN',
        notional=-750000000,
        start_date=datetime(2024, 2, 3),
        end_date=datetime(2026, 2, 3),
        calendar='TARGET+NY+LDN',
        day_count_convention='ACT/ACT(ICMA)',
        business_day_convention='ModifiedFollowing',
        settlement_lag=2,
        fixed_rate=0.055,
        fixed_frequency='1Y',
        discounting_curve='PLN.WIRON.CSA_PLN'
    )

    # Load market data
    rawMarketDataFrameDictionary = marketTools.loadMarketDataFrameDirectory(baseMarketPath)

    # 1. Base NPV (no bump)
    base_risk_conf = riskconf.RiskConfiguration(riskconf.RiskType.NPV, None, 1.0)
    marketDataFrameDictionary = marketTools.parseMarketDataFrameDictionary(rawMarketDataFrameDictionary, base_risk_conf)

    evaluationDate = du.pythonDateTime2QLDDate(trade_input.evaluation_date)
    ql.Settings.instance().evaluationDate = evaluationDate
    QLD.Settings.instance().evaluationDate = evaluationDate

    trade = parseTrades(trade_input)
    discountCurve = marketDataFrameDictionary[trade_input.discounting_curve]
    engine = ql.DiscountingBondEngine(discountCurve)
    trade.setPricingEngine(engine)
    base_npv = trade.NPV()
    print(f'Base NPV: {base_npv}')

    # 2. NPV with +10bp bump
    bump_details = riskconf.BumpDetails(None)
    bump_object = riskconf.BumpObject(
        bumpObjectName='PLN.WIRON.CSA_PLN',  # discounting_curve
        position=-1,  # -1 means parallel bump (all tenors)
        bumpSize=10/10000,
        bumpType=riskconf.BumpType.Absolute,
        details=bump_details
    )

    bump_risk_conf = riskconf.RiskConfiguration(riskconf.RiskType.NPV, [bump_object], 1.0)
    bumped_marketDataFrameDictionary = marketTools.parseMarketDataFrameDictionary(rawMarketDataFrameDictionary, bump_risk_conf)

    # test_bump(
    #     marketDataFrameDictionary['PLN.WIRON.CSA_PLN'],
    #     bumped_marketDataFrameDictionary['PLN.WIRON.CSA_PLN'],
    #     evaluationDate
    # )

    verify_bump_effect(
        marketDataFrameDictionary['PLN.WIRON.CSA_PLN'],
        bumped_marketDataFrameDictionary['PLN.WIRON.CSA_PLN'],
        trade_input
    )

    # Reprice with bumped market data
    trade_bumped = parseTrades(trade_input)
    discountCurve_bumped = bumped_marketDataFrameDictionary[trade_input.discounting_curve]
    engine_bumped = ql.DiscountingBondEngine(discountCurve_bumped)
    trade_bumped.setPricingEngine(engine_bumped)
    bumped_npv = trade_bumped.NPV()
    print(f'NPV with +10bp: {bumped_npv}')

    # 3. Calculate DV01 (Dollar Value of 1bp)
    dv01 = (bumped_npv - base_npv) / 10  # Divide by 10 because we bumped 10bp
    print(f'DV01 (approx): {dv01}')

    # 4. Try different bump sizes
    for bump_bp in [1, 5, 10, 25, 50]:
        bump_size = bump_bp / 10000  # Convert bp to decimal
        bump_object = riskconf.BumpObject('PLN.WIRON.CSA_PLN', -1, bump_size, riskconf.BumpType.Absolute, bump_details)
        bump_conf = riskconf.RiskConfiguration(riskconf.RiskType.NPV, [bump_object], 1.0)

        bumped_market = marketTools.parseMarketDataFrameDictionary(rawMarketDataFrameDictionary, bump_conf)
        trade_test = parseTrades(trade_input)
        curve_test = bumped_market[trade_input.discounting_curve]
        engine_test = ql.DiscountingBondEngine(curve_test)
        trade_test.setPricingEngine(engine_test)
        test_npv = trade_test.NPV()

        sensitivity = test_npv - base_npv
        print(f'NPV change for +{bump_bp}bp: {sensitivity}')


def test_bump(original_curve, bumped_curve, evaluationDate):
    # Compare discount factors at various dates
    test_dates = [
        evaluationDate + ql.Period(1, ql.Years),
        evaluationDate + ql.Period(2, ql.Years),
        evaluationDate + ql.Period(5, ql.Years),
        evaluationDate + ql.Period(10, ql.Years)
    ]

    print("=== Discount Factor Comparison ===")
    for test_date in test_dates:
        if test_date <= original_curve.maxDate() and test_date <= bumped_curve.maxDate():
            original_df = original_curve.discount(test_date)
            bumped_df = bumped_curve.discount(test_date)
            difference = bumped_df - original_df
            print(f"Date: {test_date}")
            print(f"  Original DF: {original_df:.8f}")
            print(f"  Bumped DF: {bumped_df:.8f}")
            print(f"  Difference: {difference:.8e}")
            print()

    print("=== Zero Rate Comparison ===")
    for test_date in test_dates:
        if test_date <= original_curve.maxDate() and test_date <= bumped_curve.maxDate():
            # Calculate time to maturity
            time_to_maturity = original_curve.dayCounter().yearFraction(evaluationDate, test_date)

            # Get zero rates
            original_rate = original_curve.zeroRate(test_date, original_curve.dayCounter(), ql.Continuous).rate()
            bumped_rate = bumped_curve.zeroRate(test_date, bumped_curve.dayCounter(), ql.Continuous).rate()

            difference_bp = (bumped_rate - original_rate) * 10000  # Convert to basis points

            print(f"Maturity: {time_to_maturity:.2f}Y ({test_date})")
            print(f"  Original Rate: {original_rate*100:.4f}%")
            print(f"  Bumped Rate: {bumped_rate*100:.4f}%")
            print(f"  Difference: {difference_bp:.1f} bp")
            print()


def verify_bump_effect(original_curve, bumped_curve, trade_input, expected_bump_bp=100):
    """Verify that the bump has been applied correctly"""
    print(f"=== Verifying {expected_bump_bp}bp bump ===")

    # Test at bond maturity (most relevant for your fixed rate bond)
    bond_maturity = du.pythonDateTime2QLDDate(trade_input.end_date)

    if bond_maturity <= original_curve.maxDate():
        original_rate = original_curve.zeroRate(bond_maturity, original_curve.dayCounter(), ql.Continuous).rate()
        bumped_rate = bumped_curve.zeroRate(bond_maturity, bumped_curve.dayCounter(), ql.Continuous).rate()

        actual_bump_bp = (bumped_rate - original_rate) * 10000

        print(f"At bond maturity ({bond_maturity}):")
        print(f"  Expected bump: {expected_bump_bp} bp")
        print(f"  Actual bump: {actual_bump_bp:.1f} bp")
        print(f"  Bump applied correctly: {abs(actual_bump_bp - expected_bump_bp) < 0.1}")

        return abs(actual_bump_bp - expected_bump_bp) < 0.1
    else:
        print("Bond maturity beyond curve range")
        return False


def test2():
    baseTradePath = "project/data/db/IRFixedRateBond"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    for i, row in trade_df.iterrows():
        trade = IRFixedRateBond(
            evaluation_date=datetime(2024, 12, 31),
            currency=row.NotionalCurrency,
            notional=row.Notional,
            start_date=row.StartDate,
            end_date=row.EndDateOrTenor,
            calendar=row.Calendar,
            day_count_convention=row.DayCount,
            business_day_convention=row.BusinessDayConvention,
            settlement_lag=row.SettlementLag,
            fixed_rate=row.FixedRate,
            fixed_frequency=row.FixedFrequency,
            discounting_curve=row.Discounting
        )

        trade.price()
        print(trade.result)


def test_risk_sensitivity():
    trade_data = {
        'evaluation_date': '2024-12-31',
        'currency': 'USD',
        'notional': 4500000000,
        'start_date': '2022-08-16',
        'end_date': '2027-08-20',
        'calendar': ['US'],
        'day_count_convention': '30/360',
        'business_day_convention': 'ModifiedFollowing',
        'settlement_lag': 5,
        'fixed_rate': 3.125,
        'fixed_frequency': '6M',
        'discounting_curve': 'USD.CREDIT.FUNDING',
        'risk_curve_name': 'USD.CREDIT.FUNDING',
        'bump_type': 'Absolute'
    }
    trade = IRFixedRateBond(
        evaluation_date=trade_data['evaluation_date'],
        currency=trade_data['currency'],
        notional=trade_data['notional'],
        start_date=trade_data['start_date'],
        end_date=trade_data['end_date'],
        calendar=trade_data['calendar'],
        day_count_convention=trade_data['day_count_convention'],
        business_day_convention=trade_data['business_day_convention'],
        settlement_lag=trade_data['settlement_lag'],
        fixed_rate=trade_data['fixed_rate'],
        fixed_frequency=trade_data['fixed_frequency'],
        discounting_curve=trade_data['discounting_curve']
    )

    # Use the new risk sensitivity methods
    bump_points = [1, 5, 10, 15, 20, 25, 30, 50]
    risk_results = trade.calculate_risk_sensitivity(bump_points=bump_points,
                                                    curve_name=trade_data['risk_curve_name'],
                                                    bump_type=trade_data['bump_type'])

    # Prepare data for plotting (include base case with 0bp bump)
    risk_dict = {
        'BP': [0] + risk_results['bump_points'],
        'NPV': [risk_results['base_npv']] + risk_results['npv_values']
    }

    plt.figure(figsize=(6, 4))
    plt.plot(risk_dict['BP'], risk_dict['NPV'], marker='o')  # line plot with markers
    plt.xlabel('Basis points')
    plt.ylabel('NPV')
    plt.title('Risk Sensitivity')
    plt.grid(True)
    plt.show()


def test3():
    baseMarketPath = "project/data/db/IRFixedRateBond"
    baseTradePath = "project/data/db/IRFixedRateBond"
    basePricingsPath = "project/data/db/IRFixedRateBond"
    outputPath = "project/data/output"
    inputPath = 'project/data/db/IRFixedRateBond/trades.xlsx'

    result = generalPricing.computePriceRisk(baseTradePath, baseMarketPath, basePricingsPath, outputPath, doParallel=False)
    print(result)


if __name__ == '__main__':
    test_risk_sensitivity()
