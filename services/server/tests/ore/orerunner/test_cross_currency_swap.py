"""
Test CrossCurrencySwap trade using ORE pricing.

Uses data from portfolio.xml: XCCY_Swap_EUR_USD_using_CrossCurrencySwap
"""

import pytest
from project.qld.ORETrade.ir.cross_currency_swap import CrossCurrencySwap


def test_cross_currency_swap_basic():
    """Test CrossCurrencySwap creation with portfolio.xml data."""
    # Data from portfolio.xml - XCCY_Swap_EUR_USD_using_CrossCurrencySwap
    trade = CrossCurrencySwap(
        evaluation_date='2016-02-05',
        start_date='2019-09-04',
        end_date='2032-09-03',
        # Leg 1 (EUR)
        currency1='EUR',
        notional1=30000000,
        index1='EUR-EURIBOR-6M',
        spread1=0.0,
        tenor1='6M',
        day_counter1='A360',
        # Leg 2 (USD)
        currency2='USD',
        notional2=33900000,
        index2='USD-LIBOR-3M',
        spread2=0.0,
        tenor2='3M',
        day_counter2='A360',
        # Exchange flags
        initial_exchange=True,
        final_exchange=True,
        # Common
        calendar='TARGET',
        payment_convention='ModifiedFollowing',
        is_in_arrears=False,
        fixing_days=2
    )

    # Verify trade was created successfully
    assert trade.currency1 == 'EUR'
    assert trade.currency2 == 'USD'
    assert trade.notional1 == 30000000.0
    assert trade.notional2 == 33900000.0
    assert trade.index1 == 'EUR-EURIBOR-6M'
    assert trade.index2 == 'USD-LIBOR-3M'
    assert trade.tenor1 == '6M'
    assert trade.tenor2 == '3M'
    assert trade.initial_exchange == True
    assert trade.final_exchange == True


def test_cross_currency_swap_pricing():
    """Test CrossCurrencySwap pricing with portfolio.xml data."""
    # Data from portfolio.xml - XCCY_Swap_EUR_USD_using_CrossCurrencySwap
    trade = CrossCurrencySwap(
        evaluation_date='2016-02-05',
        start_date='2019-09-04',
        end_date='2032-09-03',
        # Leg 1 (EUR)
        currency1='EUR',
        notional1=30000000,
        index1='EUR-EURIBOR-6M',
        spread1=0.0,
        tenor1='6M',
        day_counter1='A360',
        # Leg 2 (USD)
        currency2='USD',
        notional2=33900000,
        index2='USD-LIBOR-3M',
        spread2=0.0,
        tenor2='3M',
        day_counter2='A360',
        # Exchange flags
        initial_exchange=True,
        final_exchange=True,
        # Common
        calendar='TARGET',
        payment_convention='ModifiedFollowing'
    )

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
                'shift_tenors': ['1Y']  # '6M', '1Y', '2Y', '5Y', '10Y', '20Y'
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

    # Verify NPV is a float
    assert isinstance(trade.result['npv'], float)


def test_cross_currency_swap_validation():
    """Test CrossCurrencySwap input validation."""
    # Test that notional1 must be positive
    with pytest.raises(ValueError, match="Notional1 must be positive"):
        trade = CrossCurrencySwap(
            evaluation_date='2016-02-05',
            start_date='2019-09-04',
            end_date='2032-09-03',
            currency1='EUR',
            notional1=-30000000,
            index1='EUR-EURIBOR-6M',
            spread1=0.0,
            tenor1='6M',
            day_counter1='A360',
            currency2='USD',
            notional2=33900000,
            index2='USD-LIBOR-3M',
            spread2=0.0,
            tenor2='3M',
            day_counter2='A360',
            initial_exchange=True,
            final_exchange=True,
            calendar='TARGET',
            payment_convention='ModifiedFollowing'
        )

    # Test that currencies must be different
    with pytest.raises(ValueError, match="Leg currencies must be different"):
        trade = CrossCurrencySwap(
            evaluation_date='2016-02-05',
            start_date='2019-09-04',
            end_date='2032-09-03',
            currency1='USD',
            notional1=30000000,
            index1='USD-LIBOR-3M',
            spread1=0.0,
            tenor1='3M',
            day_counter1='A360',
            currency2='USD',  # Same as currency1 - should fail
            notional2=33900000,
            index2='USD-LIBOR-3M',
            spread2=0.0,
            tenor2='3M',
            day_counter2='A360',
            initial_exchange=True,
            final_exchange=True,
            calendar='TARGET',
            payment_convention='ModifiedFollowing'
        )

    # Test that end date must be after start date
    with pytest.raises(ValueError, match="End date must be after start date"):
        trade = CrossCurrencySwap(
            evaluation_date='2016-02-05',
            start_date='2032-09-03',
            end_date='2019-09-04',  # Before start_date - should fail
            currency1='EUR',
            notional1=30000000,
            index1='EUR-EURIBOR-6M',
            spread1=0.0,
            tenor1='6M',
            day_counter1='A360',
            currency2='USD',
            notional2=33900000,
            index2='USD-LIBOR-3M',
            spread2=0.0,
            tenor2='3M',
            day_counter2='A360',
            initial_exchange=True,
            final_exchange=True,
            calendar='TARGET',
            payment_convention='ModifiedFollowing'
        )


if __name__ == '__main__':
    test_cross_currency_swap_basic()
    test_cross_currency_swap_pricing()
    test_cross_currency_swap_validation()
