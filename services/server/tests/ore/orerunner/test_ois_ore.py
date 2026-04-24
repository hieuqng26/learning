"""
Test OISwap trade using ORE pricing.

Uses data from portfolio.xml: OIS
"""

from project.qld.ORETrade.ir.oiswap import OISwap


def test_ois_basic():
    """Test OISwap creation with portfolio.xml data."""
    # Data from portfolio.xml - OIS
    trade = OISwap(
        evaluation_date='2016-02-05',
        currency='EUR',
        notional=100000000,
        payer=False,
        start_date='2023-01-31',
        end_date='2028-02-01',
        tenor='3M',
        calendar='US',
        convention='MF',
        index='EUR-EONIA',
        spread=0.000122,
        is_in_arrears=False,
        fixing_days=2,
        day_counter='A360',
        payment_convention='MF'
    )

    # Verify trade was created successfully
    assert trade.currency == 'EUR'
    assert trade.notional == 100000000.0
    assert trade.payer == False
    assert trade.index == 'EUR-EONIA'
    assert trade.spread == 0.000122
    assert trade.tenor == '3M'


def test_ois_pricing():
    """Test OISwap pricing with portfolio.xml data."""
    # Data from portfolio.xml - OIS
    trade = OISwap(
        evaluation_date='2016-02-05',
        currency='EUR',
        notional=100000000,
        payer=False,
        start_date='2023-01-31',
        end_date='2028-02-01',
        tenor='3M',
        calendar='US',
        convention='MF',
        index='EUR-EONIA',
        spread=0.000122,
        is_in_arrears=False,
        fixing_days=2,
        day_counter='A360',
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
    test_ois_basic()
    test_ois_pricing()
