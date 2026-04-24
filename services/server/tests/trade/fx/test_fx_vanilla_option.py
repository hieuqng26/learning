import pytest
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from project.qld.engine.utils.pricing import generalPricing
from project.qld.trade.fx.fx_vanilla_option import FXVanillaOption


def make_trade():
    baseTradePath = "project/data/db/FXVanillaOption"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    row = trade_df.iloc[0]
    trade = FXVanillaOption(
        evaluation_date='31/12/2024',
        domestic_currency=row.DomesticCurrency,
        notional_currency=row.NotionalCurrency,
        foreign_currency=row.ForeignCurrency,
        expiry_date=row.ExpiryDateOrTenor,
        notional=row.Notional,
        calendar=row.Calendar,
        settlement_tenor=row.SettlementTenor,
        option_type=row.OptionType,
        strike=row.Strike,
        settlement_type=row.SettlementType,
        domestic_discounting=row.DomesticDiscounting,
        foreign_discounting=row.ForeignDiscounting,
        fx_vol_surface=row.FXVolSurface
    )
    return trade


def test_pricing_basic():
    trade = make_trade()
    trade.price()
    print(trade.result)


def test_risk_sensitivity():
    trade = make_trade()

    # Use the new risk sensitivity methods
    bump_points = [1, 5, 10, 15, 20, 25, 30, 50]
    risk_results = trade.calculate_risk_sensitivity(curve_name=trade.domestic_discounting, bump_points=bump_points)

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
    baseMarketPath = "project/data/db/FXVanillaOption"
    baseTradePath = "project/data/db/FXVanillaOption"
    basePricingsPath = "project/data/db/FXVanillaOption"
    outputPath = "project/data/output"
    result = generalPricing.computePriceRisk(baseTradePath, baseMarketPath, basePricingsPath, outputPath, doParallel=False)
    print(result)


if __name__ == '__main__':
    test_risk_sensitivity()
