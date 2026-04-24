import pytest
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from project.qld.engine.utils.pricing import generalPricing
from project.qld.trade.fx.fxspot import FXSpot


def test_fxspot_basic():
    """Test basic FX Spot instantiation and validation"""
    trade = FXSpot(
        evaluation_date='2024-12-31',
        domestic_currency='USD',
        notional_currency='USD',
        foreign_currency='EUR',
        notional=10000000,
        calendar=['US', 'TARGET'],
        settlement_date_or_tenor='2025-01-02',
        strike=1.10,
        domestic_discounting='USD.SOFR.CSA_USD',
        foreign_discounting='EUR.ESTR.CSA_EUR'
    )
    assert trade.notional == 10000000.0
    assert trade.strike == 1.10
    assert trade.domestic_currency.code() == 'USD'
    assert trade.foreign_currency.code() == 'EUR'


def test_fxspot_pricing():
    """Test FX Spot pricing functionality"""
    trade = FXSpot(
        evaluation_date='2024-12-31',
        domestic_currency='USD',
        notional_currency='USD',
        foreign_currency='EUR',
        notional=10000000,
        calendar=['US', 'TARGET'],
        settlement_date_or_tenor='2025-01-02',
        strike=1.10,
        domestic_discounting='USD.SOFR.CSA_USD',
        foreign_discounting='EUR.ESTR.CSA_EUR'
    )
    trade.price()
    assert 'npv' in trade.result
    assert isinstance(trade.result['npv'], float)


def test2():
    baseTradePath = "project/data/db/FXSpot"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    for i, row in trade_df.iterrows():
        trade = FXSpot(
            evaluation_date='31/12/2024',
            domestic_currency=row.DomesticCurrency,
            notional_currency=row.NotionalCurrency,
            foreign_currency=row.ForeignCurrency,
            notional=row.Notional,
            calendar=row.Calendar,
            settlement_date_or_tenor=row.SettlementDateOrTenor,
            # timecut=row.TimeCut,
            strike=row.Strike,
            domestic_discounting=row.DomesticDiscounting,
            foreign_discounting=row.ForeignDiscounting
        )

        trade.price()
        print(trade.result)


def test_risk_sensitivity():
    baseTradePath = "project/data/db/FXSpot"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    row = trade_df.iloc[0]
    trade = FXSpot(
        evaluation_date='31/12/2024',
        domestic_currency=row.DomesticCurrency,
        notional_currency=row.NotionalCurrency,
        foreign_currency=row.ForeignCurrency,
        notional=row.Notional,
        calendar=row.Calendar,
        settlement_date_or_tenor=row.SettlementDateOrTenor,
        # timecut=row.TimeCut,
        strike=row.Strike,
        domestic_discounting=row.DomesticDiscounting,
        foreign_discounting=row.ForeignDiscounting
    )

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
    baseMarketPath = "project/data/db/FXSpot"
    baseTradePath = "project/data/db/FXSpot"
    basePricingsPath = "project/data/db/FXSpot"
    outputPath = "project/data/output"
    result = generalPricing.computePriceRisk(baseTradePath, baseMarketPath, basePricingsPath, outputPath, doParallel=False)
    print(result)


if __name__ == '__main__':
    test_risk_sensitivity()
