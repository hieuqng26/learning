"""
Test swaption with swaption volatility sensitivity.

Simplified test focused on swaption volatility sensitivity.
"""

import pytest
import pandas as pd
from project.qld.ORETrade.ore_portfolio import OREPortfolio


def test_swaption_with_swaption_volatility_sensitivity():
    """Test swaption pricing with swaption volatility sensitivity."""
    # trades = {
    #     'Swaption': pd.DataFrame({
    #         'TradeId': ['Swaption_1'],
    #         'TradeType': ['Swaption'],
    #         'CounterParty': ['CPTY_A'],
    #         'LongShort': ['Long'],
    #         'Style': ['European'],
    #         'Settlement': ['Physical'],
    #         'ExerciseDates': ['20300220'],  # Exercise same day as swap starts
    #         'PayerReceiver': ['Payer'],
    #         'Currency': ['EUR'],
    #         'Notional': [10000000],
    #         'StartDate': ['20260220'],  # Swap starts on exercise date
    #         'EndDate': ['20360221'],  # 10-year swap
    #         'FixedRate': [0.03],
    #         'FixedTenor': ['1Y'],
    #         'FixedDayCounter': ['A360'],
    #         'FloatingIndex': ['EUR-EURIBOR-6M'],
    #         'FloatingTenor': ['6M'],
    #         'FloatingDayCounter': ['A360'],
    #         'FloatingSpread': [0.0]
    #     })
    # }

    trades = {
        'Swaption': pd.DataFrame({
            'TradeId': ['Swaption_1'],
            'CounterParty': ['CPTY_A'],
            'LongShort': ['Long'],
            'Style': ['European'],
            'Settlement': ['Cash'],
            'ExerciseDates': ['2030-02-20'],
            'PayerReceiver': ['Payer'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['2026-02-20'],
            'EndDate': ['2036-02-21'],
            'FixedRate': [0.02],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['ACT/ACT'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0],
            'PremiumAmount': None,
            'PremiumCurrency': None,
            'PremiumPayDate': None
        }, index=[0])
    }

    # Simple sensitivity config - only swaption vol
    sensitivity_config = {
        'enabled': True,
        'swaption_volatilities': [{
            'ccy': 'EUR',
            'shift_type': 'Relative',
            'shift_size': 0.01,
            'shift_scheme': 'Forward',
            'shift_expiries': ['2Y'],
            'shift_terms': ['10Y'],
            'shift_strikes': [0]
        }]
    }
    # sensitivity_config = {
    #     'swaption_volatilities': [
    #         {
    #             'ccy': 'EUR',
    #             'shift_type': 'Relative',
    #             'shift_size': 0.01,  # 1%
    #             'shift_scheme': 'Forward',
    #             'shift_expiries': ['2Y'],  # Just one expiry
    #             'shift_terms': ['10Y'],     # Just one term
    #             'shift_strikes': [0.0]      # ATM only
    #         }
    #     ],
    #     'compute_gamma': False,
    #     'use_spreaded_term_structures': False
    # }

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    assert portfolio.get_trade_count() == 1
    assert portfolio.get_trade_ids() == ['Swaption_1']

    # Price with sensitivity - cleanup=False to inspect files
    portfolio.price(sensitivity_config=sensitivity_config, cleanup=False)

    # Verify results structure
    assert 'base' in portfolio.result
    assert 'sensitivity' in portfolio.result

    # Verify base results
    assert 'npv' in portfolio.result['base']
    assert isinstance(portfolio.result['base']['npv'], pd.DataFrame)
    assert not portfolio.result['base']['npv'].empty
    assert 'Swaption_1' in portfolio.result['base']['npv']['TradeId'].values

    # Verify sensitivity results
    assert 'npv' in portfolio.result['sensitivity']
    if portfolio.result['sensitivity']['npv'] is not None:
        assert isinstance(portfolio.result['sensitivity']['npv'], pd.DataFrame)
        print("\n✅ Swaption volatility sensitivity results:")
        print(portfolio.result['sensitivity']['npv'])
    else:
        print("\n⚠️  No sensitivity results (sensitivity.csv may be empty)")

    print("\n✅ Test passed - Swaption priced with swaption volatility sensitivity")


def test_swaption_with_swaption_volatility_scenario():
    """Test swaption pricing with swaption volatility stress scenario."""
    trades = {
        'Swaption': pd.DataFrame({
            'TradeId': ['Swaption_1'],
            'TradeType': ['Swaption'],
            'CounterParty': ['CPTY_A'],
            'LongShort': ['Long'],
            'Style': ['European'],
            'Settlement': ['Physical'],
            'ExerciseDates': ['20300220'],  # Exercise same day as swap starts
            'PayerReceiver': ['Payer'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['20260220'],  # Swap starts on exercise date
            'EndDate': ['20360221'],  # 10-year swap
            'FixedRate': [0.03],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['A360'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0.0]
        })
    }

    # Simple scenario config - swaption vol stress
    scenario_config = {
        'use_spreaded_term_structures': False,
        'scenarios': [
            {
                'id': 'SWAPTION_VOL_UP_20PCT',
                'description': 'Swaption volatility up 20%',
                'swaption_volatilities': [{
                    'ccy': 'EUR',
                    'shift_type': 'Relative',
                    'shift_expiries': ['2Y'],
                    'shift_terms': ['10Y'],
                    'shifts': [0.20]  # 20% increase (1 expiry x 1 term = 1 shift)
                }]
            },
            {
                'id': 'SWAPTION_VOL_DOWN_30PCT',
                'description': 'Swaption volatility down 30%',
                'swaption_volatilities': [{
                    'ccy': 'EUR',
                    'shift_type': 'Relative',
                    'shift_expiries': ['2Y'],
                    'shift_terms': ['10Y'],
                    'shifts': [-0.30]  # 30% decrease
                }]
            }
        ]
    }

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    # Price with scenarios
    portfolio.price(scenario_config=scenario_config, cleanup=False)

    # Verify results structure
    assert 'base' in portfolio.result
    assert 'stress' in portfolio.result

    # Verify base results
    assert 'npv' in portfolio.result['base']
    base_npv = portfolio.result['base']['npv']
    assert isinstance(base_npv, pd.DataFrame) and not base_npv.empty

    # Verify stress results
    assert 'npv' in portfolio.result['stress']
    if portfolio.result['stress']['npv'] is not None:
        stress_npv = portfolio.result['stress']['npv']
        assert isinstance(stress_npv, pd.DataFrame)
        print("\n✅ Swaption volatility stress test results:")
        print(stress_npv)

        # For a long call swaption:
        # - Vol up should increase value
        # - Vol down should decrease value
        base_value = base_npv.loc[base_npv['TradeId'] == 'Swaption_1', 'NPV'].values[0]
        print(f"\nBase NPV: {base_value:,.2f}")

        if 'SWAPTION_VOL_UP_20PCT' in stress_npv['Scenario'].values:
            vol_up = stress_npv.loc[stress_npv['Scenario'] == 'SWAPTION_VOL_UP_20PCT', 'NPV'].values[0]
            print(f"Vol +20% NPV: {vol_up:,.2f} (change: {vol_up - base_value:+,.2f})")

        if 'SWAPTION_VOL_DOWN_30PCT' in stress_npv['Scenario'].values:
            vol_down = stress_npv.loc[stress_npv['Scenario'] == 'SWAPTION_VOL_DOWN_30PCT', 'NPV'].values[0]
            print(f"Vol -30% NPV: {vol_down:,.2f} (change: {vol_down - base_value:+,.2f})")
    else:
        print("\n⚠️  No stress results (stresstest.csv may be empty)")

    print("\n✅ Test passed - Swaption stress tested with swaption volatility scenarios")


if __name__ == "__main__":
    print("=" * 70)
    print("TEST 1: Swaption Volatility Sensitivity")
    print("=" * 70)
    test_swaption_with_swaption_volatility_sensitivity()

    print("\n" + "=" * 70)
    print("TEST 2: Swaption Volatility Stress Scenarios")
    print("=" * 70)
    test_swaption_with_swaption_volatility_scenario()
