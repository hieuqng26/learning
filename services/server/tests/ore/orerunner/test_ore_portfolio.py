"""
Test OREPortfolio class for portfolio-level ORE pricing.
"""

import pytest
import pandas as pd
from project.qld.ORETrade.ore_portfolio import OREPortfolio


def test_ore_portfolio_creation():
    """Test OREPortfolio creation with valid inputs."""
    # Create test data
    trades = {
        'FxForward': pd.DataFrame({
            'TradeId': ['FxFwd_1'],
            'TradeType': ['FxForward'],
            'CounterParty': ['CPTY_A'],
            'ValueDate': ['2017-02-05'],
            'BoughtCurrency': ['USD'],
            'BoughtAmount': [1000000],
            'SoldCurrency': ['EUR'],
            'SoldAmount': [920000]
        })
    }

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    assert portfolio.get_trade_count() == 1
    assert portfolio.get_trade_ids() == ['FxFwd_1']


def test_ore_portfolio_validation_empty_trades():
    """Test that empty trades raises ValueError."""
    with pytest.raises(ValueError, match="trades dictionary cannot be empty"):
        OREPortfolio(
            evaluation_date='2016-02-05',
            trades={}
        )


def test_ore_portfolio_validation_unknown_trade_type():
    """Test that unknown trade type raises ValueError."""
    trades = {
        'UnknownType': pd.DataFrame({
            'TradeId': ['Test_1'],
            'TradeType': ['UnknownType']
        })
    }

    with pytest.raises(ValueError, match="Unknown trade type"):
        OREPortfolio(
            evaluation_date='2016-02-05',
            trades=trades
        )


def test_ore_portfolio_single_fxforward():
    """Test OREPortfolio pricing with single FX Forward."""
    trades = {
        'FxForward': pd.DataFrame({
            'TradeId': ['FxFwd_1'],
            'TradeType': ['FxForward'],
            'CounterParty': ['CPTY_A'],
            'ValueDate': ['2017-02-05'],
            'BoughtCurrency': ['USD'],
            'BoughtAmount': [1000000],
            'SoldCurrency': ['EUR'],
            'SoldAmount': [920000]
        })
    }

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    portfolio.price()

    # Verify results structure
    assert 'npv' in portfolio.result
    assert 'exposures' in portfolio.result

    assert isinstance(portfolio.result['npv'], pd.DataFrame) and not portfolio.result['npv'].empty
    assert isinstance(portfolio.result['exposures'], pd.DataFrame) and not portfolio.result['exposures'].empty
    assert 'FxFwd_1' in portfolio.result['npv']['TradeId'].values


def test_ore_portfolio_single_irswap():
    """Test OREPortfolio pricing with single IR Swap."""
    trades = {
        'InterestRateSwap': pd.DataFrame({
            'TradeId': ['Swap_1'],
            'TradeType': ['InterestRateSwap'],
            'CounterParty': ['CPTY_A'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['2016-02-21'],
            'EndDate': ['2026-02-21'],
            'FixedPayer': ['false'],
            'FixedRate': [0.02],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['A360'],
            'FloatingPayer': ['true'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0.0],
            'IsInArrears': ['false'],
            'FixingDays': [2],
            'Calendar': ['TARGET'],
            'PaymentConvention': ['MF']
        })
    }

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    portfolio.price()

    # Verify results
    assert isinstance(portfolio.result['npv'], pd.DataFrame) and not portfolio.result['npv'].empty
    assert isinstance(portfolio.result['exposures'], pd.DataFrame) and not portfolio.result['exposures'].empty
    assert 'Swap_1' in portfolio.result['npv']['TradeId'].values


def test_ore_portfolio_mixed_trades():
    """Test OREPortfolio pricing with multiple trade types."""
    trades = {
        'InterestRateSwap': pd.DataFrame({
            'TradeId': ['Swap_1'],
            'TradeType': ['InterestRateSwap'],
            'CounterParty': ['CPTY_A'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['2016-02-21'],
            'EndDate': ['2026-02-21'],
            'FixedPayer': ['false'],
            'FixedRate': [0.02],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['A360'],
            'FloatingPayer': ['true'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0.0],
            'IsInArrears': ['false'],
            'FixingDays': [2],
            'Calendar': ['TARGET'],
            'PaymentConvention': ['MF']
        }),
        'FxForward': pd.DataFrame({
            'TradeId': ['FxFwd_1'],
            'TradeType': ['FxForward'],
            'CounterParty': ['CPTY_A'],
            'ValueDate': ['2017-02-05'],
            'BoughtCurrency': ['USD'],
            'BoughtAmount': [1000000],
            'SoldCurrency': ['EUR'],
            'SoldAmount': [920000]
        })
    }

    sensitivity_config = {
        'discount_curves': [
            {
                'ccy': 'EUR',
                'shift_type': 'Absolute',
                'shift_size': 0.0001,  # 1bp
                'shift_scheme': 'Forward',
                'shift_tenors': ['3M']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
            },
            {
                'ccy': 'USD',
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
        'credit_curves': [{
            'name': 'CPTY_A',
            'currency': 'USD',
            'shift_type': 'Absolute',
            'shift_size': 0.0001,
            'shift_scheme': 'Forward',
            'shift_tenors': ['1Y', '5Y']
        }],
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

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    assert portfolio.get_trade_count() == 2

    portfolio.price(sensitivity_config=sensitivity_config, scenario_config=scenario_config, cleanup=False)

    # Verify results
    assert 'npv' in portfolio.result['base']
    assert isinstance(portfolio.result['base']['npv'], pd.DataFrame) and not portfolio.result['base']['npv'].empty
    assert 'Swap_1' in portfolio.result['base']['npv']['TradeId'].values
    assert 'FxFwd_1' in portfolio.result['base']['npv']['TradeId'].values


def test_ore_portfolio_with_netting():
    """Test OREPortfolio pricing with custom netting sets."""
    trades = {
        'InterestRateSwap': pd.DataFrame({
            'TradeId': ['Swap_1'],
            'TradeType': ['InterestRateSwap'],
            'CounterParty': ['CPTY_A'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['2016-02-21'],
            'EndDate': ['2026-02-21'],
            'FixedPayer': ['false'],
            'FixedRate': [0.02],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['A360'],
            'FloatingPayer': ['true'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0.0],
            'IsInArrears': ['false'],
            'FixingDays': [2],
            'Calendar': ['TARGET'],
            'PaymentConvention': ['MF']
        }),
        'FxForward': pd.DataFrame({
            'TradeId': ['FxFwd_1'],
            'TradeType': ['FxForward'],
            'CounterParty': ['CPTY_A'],
            'ValueDate': ['2026-02-05'],
            'BoughtCurrency': ['USD'],
            'BoughtAmount': [1000000],
            'SoldCurrency': ['EUR'],
            'SoldAmount': [920000]
        }),
        'InterestRateSwap': pd.DataFrame({
            'TradeId': ['Swap_1'],
            'TradeType': ['InterestRateSwap'],
            'CounterParty': ['CPTY_C'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['2016-02-21'],
            'EndDate': ['2026-02-21'],
            'FixedPayer': ['false'],
            'FixedRate': [0.02],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['A360'],
            'FloatingPayer': ['true'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0.0],
            'IsInArrears': ['false'],
            'FixingDays': [2],
            'Calendar': ['TARGET'],
            'PaymentConvention': ['MF']
        }),
        'FxOption': pd.DataFrame({
            'TradeId': ['FxOption_1'],
            'TradeType': ['FxOption'],
            'CounterParty': ['CPTY_C'],
            'ExerciseDate': ['2026-02-08'],
            'LongShort': ['Long'],
            'OptionType': ['Call'],
            'Style': ['European'],
            'BoughtCurrency': ['EUR'],
            'BoughtAmount': [1000000],
            'SoldCurrency': ['USD'],
            'SoldAmount': [1100000]
        }),
        'Swaption': pd.DataFrame({
            'TradeId': ['Swaption_1'],
            'TradeType': ['Swaption'],
            'CounterParty': ['CPTY_A'],
            'LongShort': ['Long'],
            'Style': ['European'],
            'Settlement': ['Physical'],
            'ExerciseDates': ['20300220'],
            'PayerReceiver': ['Payer'],
            'Currency': ['EUR'],
            'Notional': [10000000],
            'StartDate': ['20260220'],
            'EndDate': ['20360221'],
            'FixedRate': [0.03],
            'FixedTenor': ['1Y'],
            'FixedDayCounter': ['A360'],
            'FloatingIndex': ['EUR-EURIBOR-6M'],
            'FloatingTenor': ['6M'],
            'FloatingDayCounter': ['A360'],
            'FloatingSpread': [0.0]
        })
    }

    sensitivity_config = {
        # 'discount_curves': [
        #     {
        #         'ccy': 'EUR',
        #         'shift_type': 'Absolute',
        #         'shift_size': 0.0001,  # 1bp
        #         'shift_scheme': 'Forward',
        #         'shift_tenors': ['3M']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
        #     },
        #     {
        #         'ccy': 'USD',
        #         'shift_type': 'Absolute',
        #         'shift_size': 0.0001,  # 1bp
        #         'shift_scheme': 'Forward',
        #         'shift_tenors': ['3M']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
        #     }
        # ],
        # 'fx_spots': [
        #     {
        #         'ccypair': 'USDEUR',
        #         'shift_type': 'Relative',
        #         'shift_size': 0.01,  # 1%
        #         'shift_scheme': 'Central'
        #     }
        # ],
        # 'fx_volatilities': [
        #     {
        #         'ccypair': 'USDEUR',
        #         'shift_type': 'Relative',
        #         'shift_size': 0.01,  # 1%
        #         'shift_scheme': 'Forward',
        #         'shift_expiries': ['1Y'],  # '2Y', '5Y'
        #         'shift_strikes': [0.0]  # ATM
        #     }
        # ],
        'swaption_volatilities': [{
            'ccy': 'EUR',
            'shift_type': 'Relative',
            'shift_expiries': ['2Y'],
            'shift_terms': ['10Y'],
            'shifts': [-0.30]
        }],
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
                'description': 'Combined: EUR rates +50bp, EURUSD down 5%, Swaption vol up 20%',
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
                }],
                'swaption_volatilities': [{
                    'ccy': 'EUR',
                    'shift_type': 'Relative',
                    'shift_expiries': ['2Y'],
                    'shift_terms': ['10Y'],
                    'shifts': [-0.30]
                }]
            }
        ],
    }

    netting_sets = pd.DataFrame({
        'NettingSetId': ['CPTY_A', 'CPTY_B', 'CPTY_C'],
        'CounterParty': ['CPTY_A', 'CPTY_B', 'CPTY_C'],
        'CSAThreshold': [100000, 110000, 120000],
        'CSAMta': [10000, 11000, 12000],
        'CollateralCurrency': ['EUR', 'EUR', 'EUR']
    })

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades,
        netting_sets=netting_sets
    )

    portfolio.price(sensitivity_config=sensitivity_config, scenario_config=scenario_config, cleanup=False)

    # Verify results
    assert 'npv' in portfolio.result['base']
    assert isinstance(portfolio.result['base']['npv'], pd.DataFrame) and not portfolio.result['base']['npv'].empty


def test_ore_portfolio_multiple_trades_same_type():
    """Test OREPortfolio with multiple trades of the same type."""
    trades = {
        'FxForward': pd.DataFrame({
            'TradeId': ['FxFwd_1', 'FxFwd_2'],
            'TradeType': ['FxForward', 'FxForward'],
            'CounterParty': ['CPTY_A', 'CPTY_A'],
            'ValueDate': ['2017-02-05', '2017-06-05'],
            'BoughtCurrency': ['USD', 'GBP'],
            'BoughtAmount': [1000000, 500000],
            'SoldCurrency': ['EUR', 'EUR'],
            'SoldAmount': [920000, 600000]
        })
    }

    portfolio = OREPortfolio(
        evaluation_date='2016-02-05',
        trades=trades
    )

    assert portfolio.get_trade_count() == 2
    assert set(portfolio.get_trade_ids()) == {'FxFwd_1', 'FxFwd_2'}

    portfolio.price()

    # Verify results
    assert isinstance(portfolio.result['npv'], pd.DataFrame) and not portfolio.result['npv'].empty
    assert isinstance(portfolio.result['exposures'], pd.DataFrame) and not portfolio.result['exposures'].empty
    assert 'FxFwd_1' in portfolio.result['npv']['TradeId'].values
    assert 'FxFwd_2' in portfolio.result['npv']['TradeId'].values


if __name__ == "__main__":
    # test_ore_portfolio_creation()
    # test_ore_portfolio_validation_empty_trades()
    # test_ore_portfolio_validation_unknown_trade_type()
    # test_ore_portfolio_single_fxforward()
    # test_ore_portfolio_single_irswap()
    # test_ore_portfolio_mixed_trades()
    test_ore_portfolio_with_netting()
    # test_ore_portfolio_multiple_trades_same_type()
