"""
Interest Rate Swap Trade Implementation using ORE.

This module provides IRS pricing using the Open Risk Engine (ORE).
"""

import pandas as pd
import project.qld.engine.parser.date as dateParser

from ..ore_base_trade import OREBaseTrade


class IRSwap(OREBaseTrade):
    """
    Interest Rate Swap trade priced using ORE.

    An IRS exchanges fixed rate payments for floating rate payments
    (or vice versa) in the same currency.
    """

    __name__ = "InterestRateSwap"

    def __init__(self, evaluation_date, currency, notional, start_date, end_date,
                 # Fixed leg parameters
                 fixed_payer, fixed_rate, fixed_tenor, fixed_day_counter,
                 # Floating leg parameters
                 floating_payer, floating_index, floating_tenor, floating_day_counter,
                 floating_spread, is_in_arrears, fixing_days,
                 # Common parameters
                 calendar, payment_convention):
        """
        Initialize Interest Rate Swap trade.

        Args:
            evaluation_date: Valuation date
            currency: Currency (e.g., 'EUR', 'USD')
            notional: Notional amount
            start_date: Start date of the swap
            end_date: End date of the swap

            Fixed leg:
            fixed_payer: True if paying fixed, False if receiving fixed
            fixed_rate: Fixed rate (in decimal, e.g., 0.02 for 2%)
            fixed_tenor: Payment frequency for fixed leg (e.g., '1Y')
            fixed_day_counter: Day count convention for fixed leg (e.g., 'A360')

            Floating leg:
            floating_payer: True if paying floating, False if receiving floating
            floating_index: Floating rate index (e.g., 'EUR-EURIBOR-6M')
            floating_tenor: Payment frequency for floating leg (e.g., '6M')
            floating_day_counter: Day count convention for floating leg
            floating_spread: Spread over index (in decimal)
            is_in_arrears: Whether fixing is in arrears
            fixing_days: Number of fixing days

            Common:
            calendar: Business day calendar (e.g., 'TARGET', 'US')
            payment_convention: Payment convention (e.g., 'MF', 'Following')
        """
        super().__init__(evaluation_date)

        self.currency = currency
        self.notional = notional
        self.start_date = start_date
        self.end_date = end_date
        self.fixed_payer = fixed_payer
        self.fixed_rate = fixed_rate
        self.fixed_tenor = fixed_tenor
        self.fixed_day_counter = fixed_day_counter
        self.floating_payer = floating_payer
        self.floating_index = floating_index
        self.floating_tenor = floating_tenor
        self.floating_day_counter = floating_day_counter
        self.floating_spread = floating_spread
        self.is_in_arrears = is_in_arrears
        self.fixing_days = fixing_days
        self.calendar = calendar
        self.payment_convention = payment_convention

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        """Parse and convert string inputs to appropriate types."""
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.currency = self.currency.upper()
        self.notional = float(self.notional)
        self.start_date = dateParser.parse_date(self.start_date)
        self.end_date = dateParser.parse_date(self.end_date)
        self.fixed_rate = float(self.fixed_rate)
        self.floating_spread = float(self.floating_spread)
        self.fixing_days = int(self.fixing_days)

        # Parse boolean flags
        if isinstance(self.fixed_payer, str):
            self.fixed_payer = self.fixed_payer.lower() in ('true', 'yes', '1')
        else:
            self.fixed_payer = bool(self.fixed_payer)

        if isinstance(self.floating_payer, str):
            self.floating_payer = self.floating_payer.lower() in ('true', 'yes', '1')
        else:
            self.floating_payer = bool(self.floating_payer)

        if isinstance(self.is_in_arrears, str):
            self.is_in_arrears = self.is_in_arrears.lower() in ('true', 'yes', '1')
        else:
            self.is_in_arrears = bool(self.is_in_arrears)

    def _validate_input(self):
        """Validate trade parameters."""
        if self.notional <= 0:
            raise ValueError("Notional must be positive")

        if self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")

        if self.start_date < self.evaluation_date:
            raise ValueError("Start date cannot be before evaluation date")

        if self.fixing_days < 0:
            raise ValueError("Fixing days must be non-negative")

        # In a standard IRS, one leg pays and the other receives
        if self.fixed_payer == self.floating_payer:
            raise ValueError("Fixed and floating payer flags should be opposite")

    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with Interest Rate Swap trade data for ORE.

        Returns:
            tuple: ('Swap', pd.DataFrame with trade parameters)
        """
        trade_df = pd.DataFrame({
            'TradeId': [self.__name__],
            'TradeType': [self.__name__],
            'CounterParty': ['CPTY_A'],
            'Currency': [self.currency],
            'Notional': [self.notional],
            'StartDate': [dateParser.ql2pydate(self.start_date).strftime('%Y-%m-%d')],
            'EndDate': [dateParser.ql2pydate(self.end_date).strftime('%Y-%m-%d')],
            'Calendar': [self.calendar],
            'PaymentConvention': [self.payment_convention],

            # Fixed leg
            'FixedPayer': [str(self.fixed_payer).lower()],
            'FixedRate': [self.fixed_rate],
            'FixedTenor': [self.fixed_tenor],
            'FixedDayCounter': [self.fixed_day_counter],

            # Floating leg
            'FloatingPayer': [str(self.floating_payer).lower()],
            'FloatingIndex': [self.floating_index],
            'FloatingTenor': [self.floating_tenor],
            'FloatingDayCounter': [self.floating_day_counter],
            'FloatingSpread': [self.floating_spread],
            'IsInArrears': [str(self.is_in_arrears).lower()],
            'FixingDays': [self.fixing_days]
        })

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
