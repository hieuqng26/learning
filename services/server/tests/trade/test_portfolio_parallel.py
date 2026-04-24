import pandas as pd
from pathlib import Path

from project.qld.trade.portfolio import Portfolio
from project.qld.engine.utils.pricing import riskConfiguration as riskconf

DATA_DIR = Path('project/data/db')


def load_data(product_name):
    input_file = DATA_DIR / f'Portfolio/{product_name}.xlsx'
    df = pd.read_excel(input_file)

    if product_name == 'IRFixedRateBond':
        df = df.rename(columns={
            'NotionalCurrency': 'currency',
            'Notional': 'notional',
            'StartDate': 'start_date',
            'EndDateOrTenor': 'end_date',
            'Calendar': 'calendar',
            'DayCount': 'day_count_convention',
            'BusinessDayConvention': 'business_day_convention',
            'SettlementLag': 'settlement_lag',
            'FixedRate': 'fixed_rate',
            'FixedFrequency': 'fixed_frequency',
            'Discounting': 'discounting_curve'
        })
        df = df.set_index('TradeID')
    return df


def test_fixed_rate_bonds():
    product_name = 'IRFixedRateBond'
    df = load_data(product_name)
    pfo = Portfolio(trade_type=product_name, evaluation_date='2024-12-31')
    pfo.load_trades_from_dataframe(df)
    pfo.price()
    print(pd.DataFrame(pfo.results['trade_results']))


def test_fixed_rate_bonds_large():

    def price_large_portfolio(trade_df, product_name, batch_size=100):
        total_results = []

        for i in range(0, len(trade_df), batch_size):
            batch_df = trade_df.iloc[i:i+batch_size]

            # Create new portfolio for each batch
            batch_portfolio = Portfolio(product_name, '2024-12-31')
            batch_portfolio.load_trades_from_dataframe(batch_df)

            batch_results = batch_portfolio.price(max_workers=4)
            total_results.extend(batch_results['trade_results'])

            print(f"Completed batch {i//batch_size + 1}: {len(batch_df)} trades")

        return total_results

    # Use for portfolios with thousands of trades
    product_name = 'IRFixedRateBond'
    df = load_data(product_name)
    large_results = price_large_portfolio(df, product_name, batch_size=2)
    print(pd.DataFrame(large_results))


def test_fixed_rate_bonds_sensitivity():
    product_name = 'IRFixedRateBond'
    df = load_data(product_name)
    pfo = Portfolio(trade_type=product_name, evaluation_date='2024-12-31')
    pfo.load_trades_from_dataframe(df)
    portfolio_risk_results = pfo.calculate_risk_sensitivity(
        curve_name=df['discounting_curve'].values[0]
    )
    print(portfolio_risk_results)


if __name__ == '__main__':
    test_fixed_rate_bonds_sensitivity()
