import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from project.qld.engine.utils.pricing import generalPricing
from project.qld.trade.ir.irswap import IRSwap


def test2():
    baseTradePath = "project/data/db/IRSwap"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    for i, row in trade_df.iterrows():
        trade = IRSwap(
            evaluation_date=datetime(2024, 12, 31),
            currency=row.NotionalCurrency,
            notional=row.Notional,
            start_date=row.StartDate,
            end_date=row.EndDateOrTenor,
            calendar=row.Calendar,
            fixing_lag=row.FixingLag,
            business_day_convention=row.BusinessDayConvention,
            type=row.Type,
            fixed_rate=row.FixedRate,
            fixed_frequency=row.FixedFrequency,
            fixed_day_count=row.FixedDayCount,
            float_index=row.FloatIndex,
            float_spread=row.FloatSpread,
            float_frequency=row.FloatFrequency,
            float_day_count=row.FloatDayCount,
            discounting_curve=row.Discounting
        )

        trade.price()
        print(trade.result)


def test_risk_sensitivity():
    baseTradePath = "project/data/db/IRSwap"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    row = trade_df.iloc[0]
    trade = IRSwap(
        evaluation_date=datetime(2024, 12, 31),
        currency=row.NotionalCurrency,
        notional=row.Notional,
        start_date=row.StartDate,
        end_date=row.EndDateOrTenor,
        calendar=row.Calendar,
        fixing_lag=row.FixingLag,
        business_day_convention=row.BusinessDayConvention,
        type=row.Type,
        fixed_rate=row.FixedRate,
        fixed_frequency=row.FixedFrequency,
        fixed_day_count=row.FixedDayCount,
        float_index=row.FloatIndex,
        float_spread=row.FloatSpread,
        float_frequency=row.FloatFrequency,
        float_day_count=row.FloatDayCount,
        discounting_curve=row.Discounting
    )

    # Use the new risk sensitivity methods
    bump_points = [1, 5, 10, 15, 20, 25, 30, 50]
    risk_results = trade.calculate_risk_sensitivity(curve_name=trade.discounting_curve, bump_points=bump_points)

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
    baseMarketPath = "data/IRSwap"
    baseTradePath = "data/IRSwap"
    basePricingsPath = "data/IRSwap"
    outputPath = "data/output"
    result = generalPricing.computePriceRisk(baseTradePath, baseMarketPath, basePricingsPath, outputPath, doParallel=False)
    print(result)


if __name__ == '__main__':
    test_risk_sensitivity()
