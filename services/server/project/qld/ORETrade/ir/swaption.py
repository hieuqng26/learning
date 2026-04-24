"""
Swaption Trade Implementation using ORE.

This module provides Interest Rate Swaption pricing using the Open Risk Engine (ORE).
Supports European, Bermudan, and American exercise styles with Cash and Physical settlement.
"""

import pandas as pd
import math
import project.qld.engine.parser.date as dateParser

from ..ore_base_trade import OREBaseTrade


class Swaption(OREBaseTrade):
    """
    Interest Rate Swaption trade priced using ORE.

    A swaption is an option to enter into an interest rate swap at a future date.
    The underlying swap exchanges fixed rate payments for floating rate payments.
    """

    __name__ = "Swaption"

    def __init__(self, evaluation_date,
                 # Option parameters
                 exercise_style, exercise_dates, long_short, settlement_type,
                 payer_receiver,
                 # Premium parameters (optional)
                 premium_amount=None, premium_currency=None, premium_pay_date=None,
                 # Underlying swap parameters
                 currency=None, notional=None, start_date=None, end_date=None,
                 # Fixed leg parameters
                 fixed_rate=None, fixed_tenor=None, fixed_day_counter=None,
                 # Floating leg parameters
                 floating_index=None, floating_tenor=None, floating_day_counter=None,
                 floating_spread=0.0,
                 # Common parameters
                 calendar='TARGET', payment_convention='MF',
                 is_in_arrears='false', fixing_days=2):
        """
        Initialize Swaption trade.

        Args:
            evaluation_date: Valuation date

            Option parameters:
            exercise_style: 'European', 'Bermudan', or 'American'
            exercise_dates: Single date for European, multiple dates for Bermudan/American
                           Can be a string (single date) or comma-separated string (multiple dates)
            long_short: 'Long' (buyer) or 'Short' (seller)
            settlement_type: 'Cash' or 'Physical'
            payer_receiver: 'Payer' (pay fixed) or 'Receiver' (receive fixed)

            Premium (optional):
            premium_amount: Premium amount paid/received
            premium_currency: Premium currency
            premium_pay_date: Premium payment date

            Underlying swap:
            currency: Swap currency (e.g., 'EUR', 'USD')
            notional: Notional amount
            start_date: Swap start date (exercise date for European)
            end_date: Swap end date (maturity)

            Fixed leg:
            fixed_rate: Fixed rate (in decimal, e.g., 0.02 for 2%)
            fixed_tenor: Payment frequency (e.g., '1Y', '6M')
            fixed_day_counter: Day count convention (e.g., 'ACT/ACT', 'A360')

            Floating leg:
            floating_index: Floating rate index (e.g., 'EUR-EURIBOR-6M')
            floating_tenor: Payment frequency (e.g., '6M', '3M')
            floating_day_counter: Day count convention
            floating_spread: Spread over index (in decimal, default 0.0)

            Common:
            calendar: Business day calendar (default 'TARGET')
            payment_convention: Payment convention (default 'MF')
            is_in_arrears: Whether fixing is in arrears (default 'false')
            fixing_days: Number of fixing days (default 2)
        """
        super().__init__(evaluation_date)

        # Option parameters
        self.exercise_style = exercise_style
        self.exercise_dates = exercise_dates
        self.long_short = long_short
        self.settlement_type = settlement_type
        self.payer_receiver = payer_receiver

        # Premium parameters
        self.premium_amount = premium_amount
        self.premium_currency = premium_currency
        self.premium_pay_date = premium_pay_date

        # Underlying swap parameters
        self.currency = currency
        self.notional = notional
        self.start_date = start_date
        self.end_date = end_date

        # Fixed leg
        self.fixed_rate = fixed_rate
        self.fixed_tenor = fixed_tenor
        self.fixed_day_counter = fixed_day_counter

        # Floating leg
        self.floating_index = floating_index
        self.floating_tenor = floating_tenor
        self.floating_day_counter = floating_day_counter
        self.floating_spread = floating_spread

        # Common
        self.calendar = calendar
        self.payment_convention = payment_convention
        self.is_in_arrears = is_in_arrears
        self.fixing_days = fixing_days

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        """Parse and convert string inputs to appropriate types."""
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)

        # Parse option parameters
        self.exercise_style = str(self.exercise_style).capitalize()
        self.long_short = str(self.long_short).capitalize()
        self.settlement_type = str(self.settlement_type).capitalize()
        self.payer_receiver = str(self.payer_receiver).capitalize()

        # Parse exercise dates - can be single date or comma-separated dates
        if isinstance(self.exercise_dates, str):
            # Already a string, will be handled in validation
            pass
        elif isinstance(self.exercise_dates, list):
            # Convert list to comma-separated string
            self.exercise_dates = ','.join([str(d) for d in self.exercise_dates])

        # Parse underlying swap parameters
        if self.currency:
            self.currency = self.currency.upper()
        if self.notional:
            self.notional = float(self.notional)
        if self.start_date:
            self.start_date = dateParser.parse_date(self.start_date)
        if self.end_date:
            self.end_date = dateParser.parse_date(self.end_date)

        # Parse fixed leg
        if self.fixed_rate is not None:
            self.fixed_rate = float(self.fixed_rate)

        # Parse floating leg
        if self.floating_spread is not None:
            self.floating_spread = float(self.floating_spread)
        if self.fixing_days is not None:
            self.fixing_days = int(self.fixing_days)

        # Parse premium if provided
        if self.premium_amount is not None:
            self.premium_amount = float(self.premium_amount)
        if self.premium_currency is not None:
            self.premium_currency = self.premium_currency.upper()
        if self.premium_pay_date is not None:
            self.premium_pay_date = dateParser.parse_date(self.premium_pay_date)

        # Parse boolean
        if isinstance(self.is_in_arrears, str):
            self.is_in_arrears = self.is_in_arrears.lower() in ('true', 'yes', '1')
        else:
            self.is_in_arrears = bool(self.is_in_arrears)

    def _validate_input(self):
        """Validate trade parameters."""
        # Validate option parameters
        if self.exercise_style not in ['European', 'Bermudan', 'American']:
            raise ValueError(f"Invalid exercise style: {self.exercise_style}. Must be European, Bermudan, or American")

        if self.long_short not in ['Long', 'Short']:
            raise ValueError(f"Invalid long/short: {self.long_short}. Must be Long or Short")

        if self.settlement_type not in ['Cash', 'Physical']:
            raise ValueError(f"Invalid settlement type: {self.settlement_type}. Must be Cash or Physical")

        if self.payer_receiver not in ['Payer', 'Receiver']:
            raise ValueError(f"Invalid payer/receiver: {self.payer_receiver}. Must be Payer or Receiver")

        # Validate exercise dates based on style
        exercise_date_list = [d.strip() for d in self.exercise_dates.split(',')]

        if self.exercise_style == 'European':
            if len(exercise_date_list) != 1:
                raise ValueError(f"European swaption must have exactly 1 exercise date, got {len(exercise_date_list)}")
        elif self.exercise_style == 'American':
            if len(exercise_date_list) != 2:
                raise ValueError(f"American swaption must have exactly 2 exercise dates (start and end), got {len(exercise_date_list)}")
        elif self.exercise_style == 'Bermudan':
            if len(exercise_date_list) < 2:
                raise ValueError(f"Bermudan swaption must have at least 2 exercise dates, got {len(exercise_date_list)}")

        # Validate underlying swap parameters
        if self.notional is not None and self.notional <= 0:
            raise ValueError("Notional must be positive")

        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValueError("End date must be after start date")

            # Parse and validate exercise dates are before swap start
            for exercise_date_str in exercise_date_list:
                exercise_date = dateParser.parse_date(exercise_date_str.strip())
                if exercise_date <= self.start_date:
                    raise ValueError(f"Exercise date {exercise_date_str} must be after swap start date")

        if self.fixing_days is not None and self.fixing_days < 0:
            raise ValueError("Fixing days must be non-negative")

        # Validate premium - if any premium field is provided, all must be provided
        premium_fields = [self.premium_amount, self.premium_currency, self.premium_pay_date]
        premium_count = sum(1 for f in premium_fields if not self._is_empty(f))
        if premium_count > 0 and premium_count < 3:
            raise ValueError("If premium is provided, all premium fields (amount, currency, pay_date) must be specified")

    @staticmethod
    def _is_empty(value):
        """
        Check if a value is empty (None, NaN, or empty string).

        Args:
            value: Value to check

        Returns:
            True if value is None, NaN, or empty string
        """
        if value is None:
            return True
        # Check for NaN (works for float NaN from pandas)
        try:
            if isinstance(value, float) and math.isnan(value):
                return True
        except (TypeError, ValueError):
            pass
        # Check for empty string
        if str(value).strip() == "":
            return True
        return False

    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with Swaption trade data for ORE.

        Returns:
            tuple: ('Swaption', pd.DataFrame with trade parameters)
        """
        trade_data = {
            'TradeId': [self.__name__],
            'TradeType': [self.__name__],
            'CounterParty': ['CPTY_A'],

            # Option parameters
            'LongShort': [self.long_short],
            'Style': [self.exercise_style],
            'Settlement': [self.settlement_type],
            'ExerciseDates': [self.exercise_dates],  # Comma-separated string

            # Underlying swap
            'Currency': [self.currency],
            'Notional': [self.notional],
            'StartDate': [dateParser.ql2pydate(self.start_date).strftime('%Y-%m-%d')],
            'EndDate': [dateParser.ql2pydate(self.end_date).strftime('%Y-%m-%d')],
            'Calendar': [self.calendar],
            'PaymentConvention': [self.payment_convention],
            'PayerReceiver': [self.payer_receiver],

            # Fixed leg
            'FixedRate': [self.fixed_rate],
            'FixedTenor': [self.fixed_tenor],
            'FixedDayCounter': [self.fixed_day_counter],

            # Floating leg
            'FloatingIndex': [self.floating_index],
            'FloatingTenor': [self.floating_tenor],
            'FloatingDayCounter': [self.floating_day_counter],
            'FloatingSpread': [self.floating_spread],
            'IsInArrears': [str(self.is_in_arrears).lower()],
            'FixingDays': [self.fixing_days]
        }

        # Add premium fields if provided
        if not self._is_empty(self.premium_amount):
            trade_data['PremiumAmount'] = [self.premium_amount]
            trade_data['PremiumCurrency'] = [self.premium_currency]
            trade_data['PremiumPayDate'] = [dateParser.ql2pydate(self.premium_pay_date).strftime('%Y-%m-%d')]

        trade_df = pd.DataFrame(trade_data)

        return (self.__name__, trade_df)

    def _filter_epe_dates(self, exposure_df):
        """
        Filter exposure DataFrame to include only relevant dates.

        Args:
            exposure_df (pd.DataFrame): DataFrame with exposure data including 'Date' column.
        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        exposure_df['Date'] = pd.to_datetime(exposure_df['Date'])
        start_date = dateParser.ql2npdate(self.start_date)
        end_date = dateParser.ql2npdate(self.end_date)
        filtered_df = exposure_df[(exposure_df['Date'] >= start_date) & (exposure_df['Date'] <= end_date)]
        return filtered_df
