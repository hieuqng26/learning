import pytest
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

from project.qld.engine.utils.pricing import generalPricing
from project.qld.trade.equity.equity_forward import EQForward
from project.qld.trade.commodity.commodity_forward import COMForward
from project.qld.trade.crypto.crypto_forward import CRYPTOForward


def make_trade(Product):
    baseTradePath = f"project/data/db/{Product.__name__}"
    trade_df = pd.read_excel(baseTradePath+'/trades.xlsx', skiprows=3)

    row = trade_df.iloc[0]
    trade = Product(
        evaluation_date='31/12/2024',
        ticker=row.Ticker,
        currency=row.Currency,
        notional=row.Notional,
        calendar=row.Calendar,
        settlement_date_or_tenor=row.SettlementDateOrTenor,
        strike=row.Strike,
        discounting=row.Discounting,
    )
    return trade


def test_pricing_basic(Product):
    trade = make_trade(Product)
    trade.price()
    print(trade.result)


def test_risk_sensitivity(Product):
    trade = make_trade(Product)

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


if __name__ == '__main__':
    test_pricing_basic(EQForward)
    test_risk_sensitivity(EQForward)

    test_pricing_basic(COMForward)
    test_risk_sensitivity(COMForward)

    test_pricing_basic(CRYPTOForward)
    test_risk_sensitivity(CRYPTOForward)
