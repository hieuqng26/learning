"""
Test Swaption trade using ORE pricing.

Tests European, Bermudan, and American exercise styles.
Uses data structure similar to ORE examples in doc/ORE/Examples/Products/Example_Trades/
"""

import pytest
from project.qld.ORETrade.ir.swaption import Swaption


def test_swaption_european_basic():
    """Test European Swaption creation with single exercise date."""
    trade = Swaption(
        evaluation_date='2016-02-05',
        # Option parameters
        exercise_style='European',
        exercise_dates='2033-02-20',
        long_short='Long',
        settlement_type='Cash',
        payer_receiver='Payer',
        # Underlying swap parameters
        currency='EUR',
        notional=10000000,
        start_date='2033-02-20',
        end_date='2043-02-21',
        # Fixed leg
        fixed_rate=0.02,
        fixed_tenor='1Y',
        fixed_day_counter='ACT/ACT',
        # Floating leg
        floating_index='EUR-EURIBOR-3M',
        floating_tenor='3M',
        floating_day_counter='A360',
        floating_spread=0.0,
        # Common
        calendar='TARGET',
        payment_convention='MF',
        is_in_arrears=False,
        fixing_days=2
    )

    # Verify option parameters
    assert trade.exercise_style == 'European'
    assert trade.exercise_dates == '2033-02-20'
    assert trade.long_short == 'Long'
    assert trade.settlement_type == 'Cash'
    assert trade.payer_receiver == 'Payer'

    # Verify swap parameters
    assert trade.currency == 'EUR'
    assert trade.notional == 10000000.0
    assert trade.fixed_rate == 0.02
    assert trade.floating_index == 'EUR-EURIBOR-3M'


def test_swaption_bermudan():
    """Test Bermudan Swaption with multiple exercise dates."""
    trade = Swaption(
        evaluation_date='2016-02-05',
        # Option parameters
        exercise_style='Bermudan',
        exercise_dates='2033-02-20,2034-02-20,2035-02-20',  # Multiple dates
        long_short='Long',
        settlement_type='Physical',
        payer_receiver='Receiver',
        # Underlying swap parameters
        currency='USD',
        notional=5000000,
        start_date='2033-02-20',
        end_date='2043-02-21',
        # Fixed leg
        fixed_rate=0.03,
        fixed_tenor='6M',
        fixed_day_counter='A360',
        # Floating leg
        floating_index='USD-LIBOR-3M',
        floating_tenor='3M',
        floating_day_counter='A360'
    )

    # Verify Bermudan-specific parameters
    assert trade.exercise_style == 'Bermudan'
    assert '2033-02-20' in trade.exercise_dates
    assert '2034-02-20' in trade.exercise_dates
    assert '2035-02-20' in trade.exercise_dates
    assert trade.settlement_type == 'Physical'
    assert trade.payer_receiver == 'Receiver'


def test_swaption_american():
    """Test American Swaption with exercise period (start and end dates)."""
    trade = Swaption(
        evaluation_date='2016-02-05',
        # Option parameters
        exercise_style='American',
        exercise_dates='2033-02-20,2035-02-20',  # Start and end of exercise period
        long_short='Short',
        settlement_type='Cash',
        payer_receiver='Payer',
        # Underlying swap parameters
        currency='GBP',
        notional=3000000,
        start_date='2033-02-20',
        end_date='2043-02-21',
        # Fixed leg
        fixed_rate=0.025,
        fixed_tenor='1Y',
        fixed_day_counter='ACT/ACT',
        # Floating leg
        floating_index='GBP-LIBOR-6M',
        floating_tenor='6M',
        floating_day_counter='ACT/365'
    )

    # Verify American-specific parameters
    assert trade.exercise_style == 'American'
    assert trade.long_short == 'Short'
    # Should have exactly 2 dates for American
    exercise_date_list = [d.strip() for d in trade.exercise_dates.split(',')]
    assert len(exercise_date_list) == 2


def test_swaption_with_premium():
    """Test Swaption with optional premium."""
    trade = Swaption(
        evaluation_date='2016-02-05',
        # Option parameters
        exercise_style='European',
        exercise_dates='2033-02-20',
        long_short='Long',
        settlement_type='Cash',
        payer_receiver='Payer',
        # Premium
        premium_amount=1090000,
        premium_currency='EUR',
        premium_pay_date='2026-02-20',
        # Underlying swap parameters
        currency='EUR',
        notional=10000000,
        start_date='2033-02-20',
        end_date='2043-02-21',
        # Fixed leg
        fixed_rate=0.02,
        fixed_tenor='1Y',
        fixed_day_counter='ACT/ACT',
        # Floating leg
        floating_index='EUR-EURIBOR-3M',
        floating_tenor='3M',
        floating_day_counter='A360'
    )

    # Verify premium parameters
    assert trade.premium_amount == 1090000.0
    assert trade.premium_currency == 'EUR'
    assert trade.premium_pay_date is not None


def test_swaption_validation_exercise_style():
    """Test that invalid exercise style is rejected."""
    with pytest.raises(ValueError, match="Invalid exercise style"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='Invalid',
            exercise_dates='2033-02-20',
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_european_dates():
    """Test that European swaption must have exactly one exercise date."""
    with pytest.raises(ValueError, match="European swaption must have exactly 1 exercise date"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='European',
            exercise_dates='2033-02-20,2034-02-20',  # Too many dates
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_american_dates():
    """Test that American swaption must have exactly two exercise dates."""
    with pytest.raises(ValueError, match="American swaption must have exactly 2 exercise dates"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='American',
            exercise_dates='2033-02-20',  # Need 2 dates
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_bermudan_dates():
    """Test that Bermudan swaption must have at least two exercise dates."""
    with pytest.raises(ValueError, match="Bermudan swaption must have at least 2 exercise dates"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='Bermudan',
            exercise_dates='2033-02-20',  # Need at least 2 dates
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_notional():
    """Test that notional must be positive."""
    with pytest.raises(ValueError, match="Notional must be positive"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='European',
            exercise_dates='2033-02-20',
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            currency='EUR',
            notional=-10000000,  # Negative notional
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_settlement_type():
    """Test that settlement type must be valid."""
    with pytest.raises(ValueError, match="Invalid settlement type"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='European',
            exercise_dates='2033-02-20',
            long_short='Long',
            settlement_type='Invalid',  # Invalid settlement
            payer_receiver='Payer',
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_payer_receiver():
    """Test that payer/receiver must be valid."""
    with pytest.raises(ValueError, match="Invalid payer/receiver"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='European',
            exercise_dates='2033-02-20',
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Invalid',  # Invalid payer/receiver
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_premium_incomplete():
    """Test that all premium fields must be provided together."""
    with pytest.raises(ValueError, match="If premium is provided, all premium fields"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='European',
            exercise_dates='2033-02-20',
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            # Incomplete premium - only amount, missing currency and pay_date
            premium_amount=1090000,
            currency='EUR',
            notional=10000000,
            start_date='2033-02-20',
            end_date='2043-02-21',
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_validation_date_ordering():
    """Test that end date must be after start date."""
    with pytest.raises(ValueError, match="End date must be after start date"):
        Swaption(
            evaluation_date='2016-02-05',
            exercise_style='European',
            exercise_dates='2033-02-20',
            long_short='Long',
            settlement_type='Cash',
            payer_receiver='Payer',
            currency='EUR',
            notional=10000000,
            start_date='2043-02-21',  # After end date
            end_date='2033-02-20',    # Before start date
            fixed_rate=0.02,
            fixed_tenor='1Y',
            fixed_day_counter='ACT/ACT',
            floating_index='EUR-EURIBOR-3M',
            floating_tenor='3M',
            floating_day_counter='A360'
        )


def test_swaption_dataframe_structure():
    """Test that DataFrame is constructed correctly."""
    trade = Swaption(
        evaluation_date='2016-02-05',
        exercise_style='European',
        exercise_dates='2033-02-20',
        long_short='Long',
        settlement_type='Cash',
        payer_receiver='Payer',
        currency='EUR',
        notional=10000000,
        start_date='2033-02-20',
        end_date='2043-02-21',
        fixed_rate=0.02,
        fixed_tenor='1Y',
        fixed_day_counter='ACT/ACT',
        floating_index='EUR-EURIBOR-3M',
        floating_tenor='3M',
        floating_day_counter='A360'
    )

    # Get DataFrame
    trade_type, df = trade._build_trade_dataframe()

    # Verify trade type
    assert trade_type == 'Swaption'

    # Verify required columns exist
    required_columns = [
        'TradeId', 'TradeType', 'CounterParty',
        'LongShort', 'Style', 'Settlement', 'ExerciseDates', 'PayerReceiver',
        'Currency', 'Notional', 'StartDate', 'EndDate',
        'FixedRate', 'FixedTenor', 'FixedDayCounter',
        'FloatingIndex', 'FloatingTenor', 'FloatingDayCounter'
    ]

    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    # Verify data types and values
    assert df['TradeId'].iloc[0] == 'Swaption'
    assert df['TradeType'].iloc[0] == 'Swaption'
    assert df['Style'].iloc[0] == 'European'
    assert df['LongShort'].iloc[0] == 'Long'
    assert df['Settlement'].iloc[0] == 'Cash'
    assert df['PayerReceiver'].iloc[0] == 'Payer'
    assert df['Currency'].iloc[0] == 'EUR'
    assert df['Notional'].iloc[0] == 10000000
    assert df['FixedRate'].iloc[0] == 0.02
    assert df['FloatingIndex'].iloc[0] == 'EUR-EURIBOR-3M'


def test_swaption_pricing():
    """Test Swaption pricing with ORE (European payer swaption)."""
    trade = Swaption(
        evaluation_date='2016-02-05',
        # Option parameters
        exercise_style='European',
        exercise_dates='2036-02-20',
        long_short='Long',
        settlement_type='Cash',
        payer_receiver='Payer',
        # Underlying swap parameters
        currency='EUR',
        notional=10000000,
        start_date='2033-02-20',
        end_date='2043-02-21',
        # Fixed leg
        fixed_rate=0.02,
        fixed_tenor='1Y',
        fixed_day_counter='ACT/ACT',
        # Floating leg
        floating_index='EUR-EURIBOR-3M',
        floating_tenor='3M',
        floating_day_counter='A360',
        floating_spread=0.0,
        # Common
        calendar='TARGET',
        payment_convention='MF'
    )

    # Price the trade using ORE
    trade.price(cleanup=False)

    # Verify results structure
    assert 'npv' in trade.result
    assert 'cva' in trade.result
    assert 'dva' in trade.result
    assert 'exposures' in trade.result

    # Verify NPV is a float
    assert isinstance(trade.result['npv'], float)


if __name__ == '__main__':
    # # Run basic tests
    # test_swaption_european_basic()
    # test_swaption_bermudan()
    # test_swaption_american()
    # test_swaption_with_premium()
    # test_swaption_dataframe_structure()

    # # Run validation tests
    # test_swaption_validation_exercise_style()
    # test_swaption_validation_european_dates()
    # test_swaption_validation_american_dates()
    # test_swaption_validation_bermudan_dates()
    # test_swaption_validation_notional()
    # test_swaption_validation_settlement_type()
    # test_swaption_validation_payer_receiver()
    # test_swaption_validation_premium_incomplete()
    # test_swaption_validation_date_ordering()

    # Run pricing tests (requires ORE setup)
    test_swaption_pricing()

    print("\nAll tests passed!")
