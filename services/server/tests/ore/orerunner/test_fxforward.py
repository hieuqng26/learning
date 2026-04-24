"""
Test FXForward trade using ORE pricing.

Uses data from portfolio.xml: FXFWD_EURUSD_10Y
"""

import pytest
from project.qld.ORETrade.fx.fxforward import FXForward


def test_fxforward_basic():
    """Test FXForward creation with portfolio.xml data."""
    # Data from portfolio.xml - FXFWD_EURUSD_10Y (cash settlement)
    trade = FXForward(
        evaluation_date='2016-02-05',
        value_date='2033-02-20',
        bought_currency='EUR',
        bought_amount=1000000,
        sold_currency='USD',
        sold_amount=1100000,
        settlement='Cash',
        settlement_currency='USD',
        fx_index='FX-TR20H-EUR-USD',
        settlement_date='2033-02-24',
        payment_lag='2D',
        payment_calendar='USD',
        payment_convention='Following'
    )

    # Verify trade was created successfully
    assert trade.bought_currency == 'EUR'
    assert trade.sold_currency == 'USD'
    assert trade.bought_amount == 1000000.0
    assert trade.sold_amount == 1100000.0
    assert trade.settlement == 'Cash'
    assert trade.settlement_currency == 'USD'
    assert trade.fx_index == 'FX-TR20H-EUR-USD'


def test_fxforward_physical_settlement():
    """Test FXForward with physical settlement (simpler case)."""
    trade = FXForward(
        evaluation_date='2016-02-05',
        value_date='2033-02-20',
        bought_currency='EUR',
        bought_amount=1000000,
        sold_currency='USD',
        sold_amount=1100000,
        settlement='Physical'
    )

    # Verify trade was created successfully
    assert trade.bought_currency == 'EUR'
    assert trade.sold_currency == 'USD'
    assert trade.settlement == 'Physical'


def test_fxforward_pricing():
    """Test FXForward pricing with portfolio.xml data."""
    # Data from portfolio.xml - FXFWD_EURUSD_10Y
    trade = FXForward(
        evaluation_date='2016-02-05',
        value_date='2033-02-20',
        bought_currency='EUR',
        bought_amount=1000000,
        sold_currency='USD',
        sold_amount=1100000,
        settlement='Cash',
        settlement_currency='USD',
        fx_index='FX-TR20H-EUR-USD',
        settlement_date='2033-02-24',
        payment_lag='2D',
        payment_calendar='USD',
        payment_convention='Following'
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


def test_fxforward_validation():
    """Test FXForward input validation."""
    # Test that bought amount must be positive
    with pytest.raises(ValueError, match="Bought amount must be positive"):
        trade = FXForward(
            evaluation_date='2016-02-05',
            value_date='2033-02-20',
            bought_currency='EUR',
            bought_amount=-1000000,
            sold_currency='USD',
            sold_amount=1100000,
        )

    # Test that currencies must be different
    with pytest.raises(ValueError, match="Bought and sold currencies must be different"):
        trade = FXForward(
            evaluation_date='2016-02-05',
            value_date='2033-02-20',
            bought_currency='USD',
            bought_amount=1000000,
            sold_currency='USD',
            sold_amount=1100000,
        )

    # Test that settlement must be valid
    with pytest.raises(ValueError, match="Settlement must be 'Physical' or 'Cash'"):
        trade = FXForward(
            evaluation_date='2016-02-05',
            value_date='2033-02-20',
            bought_currency='EUR',
            bought_amount=1000000,
            sold_currency='USD',
            sold_amount=1100000,
            settlement='Invalid'
        )

    # Test that cash settlement requires settlement currency
    with pytest.raises(ValueError, match="Settlement currency is required for cash settlement"):
        trade = FXForward(
            evaluation_date='2016-02-05',
            value_date='2033-02-20',
            bought_currency='EUR',
            bought_amount=1000000,
            sold_currency='USD',
            sold_amount=1100000,
            settlement='Cash'
        )

    # Test that cash settlement requires FX index
    with pytest.raises(ValueError, match="FX index is required for cash settlement"):
        trade = FXForward(
            evaluation_date='2016-02-05',
            value_date='2033-02-20',
            bought_currency='EUR',
            bought_amount=1000000,
            sold_currency='USD',
            sold_amount=1100000,
            settlement='Cash',
            settlement_currency='USD'
        )


if __name__ == '__main__':
    test_fxforward_basic()
    test_fxforward_physical_settlement()
    test_fxforward_pricing()
    test_fxforward_validation()
