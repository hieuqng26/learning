"""
Test IRSwap trade using ORE pricing.

Uses data from portfolio.xml: Swap_20y
"""

from project.qld.ORETrade.ir.irswap import IRSwap


def test_irswap_basic():
    """Test IRSwap creation with portfolio.xml data."""
    # Data from portfolio.xml - Swap_20y
    trade = IRSwap(
        evaluation_date='2016-02-05',
        currency='EUR',
        notional=10000000,
        start_date='2023-02-21',
        end_date='2043-02-21',
        # Fixed leg
        fixed_payer=False,
        fixed_rate=0.021,
        fixed_tenor='1Y',
        fixed_day_counter='A360',
        # Floating leg
        floating_payer=True,
        floating_index='EUR-EURIBOR-6M',
        floating_tenor='6M',
        floating_day_counter='A360',
        floating_spread=0.0,
        is_in_arrears=False,
        fixing_days=2,
        # Common
        calendar='TARGET',
        payment_convention='MF'
    )

    # Verify trade was created successfully
    assert trade.currency == 'EUR'
    assert trade.notional == 10000000.0
    assert trade.fixed_payer == False
    assert trade.floating_payer == True
    assert trade.fixed_rate == 0.021
    assert trade.floating_index == 'EUR-EURIBOR-6M'
    assert trade.fixed_tenor == '1Y'
    assert trade.floating_tenor == '6M'


def test_irswap_pricing():
    """Test IRSwap pricing with portfolio.xml data."""
    # Data from portfolio.xml - Swap_20y
    trade = IRSwap(
        evaluation_date='2016-02-05',
        currency='EUR',
        notional=10000000,
        start_date='2023-02-21',
        end_date='2043-02-21',
        # Fixed leg
        fixed_payer=False,
        fixed_rate=0.021,
        fixed_tenor='1Y',
        fixed_day_counter='A360',
        # Floating leg
        floating_payer=True,
        floating_index='EUR-EURIBOR-6M',
        floating_tenor='6M',
        floating_day_counter='A360',
        floating_spread=0.0,
        is_in_arrears=False,
        fixing_days=2,
        # Common
        calendar='TARGET',
        payment_convention='MF'
    )

    # Price the trade using ORE
    trade.price()

    # Verify results structure
    assert 'npv' in trade.result
    assert 'cva' in trade.result
    assert 'dva' in trade.result
    assert 'exposures' in trade.result

    # Verify NPV is a float
    assert isinstance(trade.result['npv'], float)


if __name__ == "__main__":
    test_irswap_basic()
    test_irswap_pricing()
