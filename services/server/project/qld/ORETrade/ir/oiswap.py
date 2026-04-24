"""
OIS (Overnight Index Swap) Trade Implementation using ORE.

This module provides OIS pricing using the Open Risk Engine (ORE).
"""

import pandas as pd
import project.qld.engine.parser.date as dateParser

from ..ore_base_trade import OREBaseTrade


class OISwap(OREBaseTrade):
    """
    Overnight Index Swap (OIS) trade priced using ORE.

    An OIS is an interest rate swap where the floating leg is tied
    to an overnight rate index (e.g., EONIA, SOFR).
    """

    __name__ = "OvernightIndexSwap"

    def __init__(self, evaluation_date, currency, notional, payer, start_date, end_date,
                 tenor, calendar, convention, index, spread, is_in_arrears, fixing_days,
                 day_counter, payment_convention):
        """
        Initialize OIS trade.

        Args:
            evaluation_date: Valuation date
            currency: Currency (e.g., 'EUR', 'USD')
            notional: Notional amount
            payer: True if paying floating, False if receiving floating
            start_date: Start date of the swap
            end_date: End date of the swap
            tenor: Payment frequency (e.g., '3M', '6M')
            calendar: Business day calendar (e.g., 'TARGET', 'US')
            convention: Business day convention (e.g., 'MF', 'Following')
            index: Floating rate index (e.g., 'EUR-EONIA', 'USD-SOFR')
            spread: Spread over index (in decimal, e.g., 0.001 for 10bp)
            is_in_arrears: Whether fixing is in arrears
            fixing_days: Number of fixing days
            day_counter: Day count convention (e.g., 'A360', 'ACT/360')
            payment_convention: Payment convention
        """
        super().__init__(evaluation_date)

        self.currency = currency
        self.notional = notional
        self.payer = payer
        self.start_date = start_date
        self.end_date = end_date
        self.tenor = tenor
        self.calendar = calendar
        self.convention = convention
        self.index = index
        self.spread = spread
        self.is_in_arrears = is_in_arrears
        self.fixing_days = fixing_days
        self.day_counter = day_counter
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
        self.spread = float(self.spread)
        self.fixing_days = int(self.fixing_days)

        # Parse boolean payer flag
        if isinstance(self.payer, str):
            self.payer = self.payer.lower() in ('true', 'yes', '1')
        else:
            self.payer = bool(self.payer)

        # Parse boolean is_in_arrears
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

    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with OIS trade data for ORE.

        Returns:
            tuple: ('Swap', pd.DataFrame with trade parameters)

        Note: OIS is represented as a Swap with only a floating leg in ORE.
        """
        trade_df = pd.DataFrame({
            'TradeId': [self.__name__],
            'TradeType': [self.__name__],
            'CounterParty': ['CPTY_A'],
            'Currency': [self.currency],
            'Notional': [self.notional],
            'Payer': [str(self.payer).lower()],
            'StartDate': [dateParser.ql2pydate(self.start_date).strftime('%Y-%m-%d')],
            'EndDate': [dateParser.ql2pydate(self.end_date).strftime('%Y-%m-%d')],
            'Tenor': [self.tenor],
            'Calendar': [self.calendar],
            'Convention': [self.convention],
            'FloatingIndex': [self.index],
            'FloatingSpread': [self.spread],
            'IsInArrears': [str(self.is_in_arrears).lower()],
            'FixingDays': [self.fixing_days],
            'DayCounter': [self.day_counter],
            'PaymentConvention': [self.payment_convention],
            # For OIS, we only have a floating leg
            'LegType': ['Floating'],
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
