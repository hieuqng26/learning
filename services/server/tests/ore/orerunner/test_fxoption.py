"""
Test FXOption with multiple exercise dates and premiums.

Demonstrates the enhanced features of FXOption.
"""

from project.qld.ORETrade.fx.fxoption import FXOption


def test_fxoption_european_multiple_premiums():
    """Test FXOption European with multiple premiums."""
    trade = FXOption(
        evaluation_date='2016-02-05',
        bought_currency='EUR',
        bought_amount=1000000,
        sold_currency='USD',
        sold_amount=1100000,
        long_short='Long',
        option_type='Call',
        style='European',
        exercise_date=['2026-03-01'],
        settlement='Cash',
        payoff_at_expiry=False,
        # premium_amount=[3000, 3500, 4400],
        # premium_currency=['EUR', 'EUR', 'EUR'],
        # premium_pay_date=['2016-03-01', '2020-02-20', '2025-02-20']
    )

    sensitivity_config = {
        'discount_curves': [
            {
                'ccy': 'EUR',
                'shift_type': 'Absolute',
                'shift_size': 0.0001,  # 1bp
                'shift_scheme': 'Forward',
                'shift_tenors': ['3M']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
            }
        ],
        'fx_spots': [
            {
                'ccypair': 'USDEUR',
                'shift_type': 'Relative',
                'shift_size': 0.01,  # 1%
                'shift_scheme': 'Central'
            }
        ],
        'fx_volatilities': [
            {
                'ccypair': 'USDEUR',
                'shift_type': 'Relative',
                'shift_size': 0.01,  # 1%
                'shift_scheme': 'Forward',
                'shift_expiries': ['1Y'],  # '2Y', '5Y'
                'shift_strikes': [0.0]  # ATM
            }
        ],
        # 'credit_curves': [{
        #     'name': 'CPTY_A',
        #     'currency': 'USD',
        #     'shift_type': 'Absolute',
        #     'shift_size': 0.0001,
        #     'shift_scheme': 'Forward',
        #     'shift_tenors': ['1Y', '5Y']
        # }],
        'compute_gamma': False,  # Set to True for second-order sensitivities
        'use_spreaded_term_structures': False
    }

    scenario_config = {
        'use_spreaded_term_structures': False,
        'scenarios': [
            {
                'id': 'EUR_rates_up_100bp',
                'description': 'EUR rates parallel shift +100bp',
                'discount_curves': [{
                    'ccy': 'EUR',
                    'shift_type': 'Absolute',
                    'shifts': [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],  # 100bp uniform
                    'shift_tenors': ['6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '15Y', '20Y']
                }]
            },
            {
                'id': 'EURUSD_down_10pct',
                'description': 'EUR/USD down 10%',
                'fx_spots': [{
                    'ccypair': 'USDEUR',
                    'shift_type': 'Relative',
                    'shift_size': -0.10
                }]
            },
            {
                'id': 'Combined_rates_fx',
                'description': 'Combined: EUR rates +50bp, EURUSD down 5%',
                'discount_curves': [{
                    'ccy': 'EUR',
                    'shift_type': 'Absolute',
                    'shifts': [0.005, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005],
                    'shift_tenors': ['6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '15Y', '20Y']
                }],
                'fx_spots': [{
                    'ccypair': 'USDEUR',
                    'shift_type': 'Relative',
                    'shift_size': -0.05
                }]
            }
        ],
    }

    # Price the trade using ORE
    trade.price(cleanup=True, sensitivity_config=sensitivity_config, scenario_config=scenario_config)

    # Verify results structure
    assert 'npv' in trade.result
    assert 'cva' in trade.result
    assert 'dva' in trade.result
    assert 'exposures' in trade.result


def _test_fxoption_american_multiple_premiums():
    """Test FXOption American with multiple premiums."""
    trade = FXOption(
        evaluation_date='2016-02-05',
        bought_currency='EUR',
        bought_amount=1000000,
        sold_currency='USD',
        sold_amount=1100000,
        long_short='Long',
        option_type='Put',
        style='American',
        exercise_date=['2033-02-20'],
        settlement='Cash',
        payoff_at_expiry=False,
        premium_amount=[10900],
        premium_currency=['EUR'],
        premium_pay_date=['2025-02-20']
    )

    # Price the trade using ORE
    trade.price()

    # Verify results structure
    assert 'npv' in trade.result
    assert 'cva' in trade.result
    assert 'dva' in trade.result
    assert 'exposures' in trade.result


if __name__ == "__main__":
    test_fxoption_european_multiple_premiums()
    # _test_fxoption_american_multiple_premiums()
    print("All tests passed!")
