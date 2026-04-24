"""
Cross-Currency Swap Trade Implementation using ORE.

This module provides Cross-Currency Swap pricing using the Open Risk Engine (ORE).
"""

import pandas as pd
import project.qld.engine.parser.date as dateParser

from ..ore_base_trade import OREBaseTrade


class CrossCurrencySwap(OREBaseTrade):
    """
    Cross-Currency Swap trade priced using ORE.

    A CCS exchanges cash flows in two different currencies, typically
    with floating rates on both legs. Can include initial and final
    notional exchanges.
    """

    __name__ = "CrossCurrencySwap"

    def __init__(self, evaluation_date, start_date, end_date,
                 # Leg 1 parameters
                 currency1, notional1, index1, spread1, tenor1, day_counter1,
                 # Leg 2 parameters
                 currency2, notional2, index2, spread2, tenor2, day_counter2,
                 # Exchange flags
                 initial_exchange, final_exchange,
                 # Common parameters
                 calendar, payment_convention, is_in_arrears=False, fixing_days=2):
        """
        Initialize Cross-Currency Swap trade.

        Args:
            evaluation_date: Valuation date
            start_date: Start date of the swap
            end_date: End date of the swap

            Leg 1 (typically domestic/receive leg):
            currency1: Currency for leg 1 (e.g., 'EUR')
            notional1: Notional amount for leg 1
            index1: Floating rate index for leg 1 (e.g., 'EUR-EURIBOR-6M')
            spread1: Spread over index for leg 1 (in decimal)
            tenor1: Payment frequency for leg 1 (e.g., '6M')
            day_counter1: Day count convention for leg 1 (e.g., 'A360')

            Leg 2 (typically foreign/pay leg):
            currency2: Currency for leg 2 (e.g., 'USD')
            notional2: Notional amount for leg 2
            index2: Floating rate index for leg 2 (e.g., 'USD-LIBOR-3M')
            spread2: Spread over index for leg 2 (in decimal)
            tenor2: Payment frequency for leg 2 (e.g., '3M')
            day_counter2: Day count convention for leg 2

            Exchange flags:
            initial_exchange: Exchange notionals at start (True/False)
            final_exchange: Exchange notionals at maturity (True/False)

            Common:
            calendar: Business day calendar
            payment_convention: Payment convention (e.g., 'ModifiedFollowing')
            is_in_arrears: Whether fixing is in arrears (default: False)
            fixing_days: Number of fixing days (default: 2)
        """
        super().__init__(evaluation_date)

        self.start_date = start_date
        self.end_date = end_date
        self.currency1 = currency1
        self.notional1 = notional1
        self.index1 = index1
        self.spread1 = spread1
        self.tenor1 = tenor1
        self.day_counter1 = day_counter1
        self.currency2 = currency2
        self.notional2 = notional2
        self.index2 = index2
        self.spread2 = spread2
        self.tenor2 = tenor2
        self.day_counter2 = day_counter2
        self.initial_exchange = initial_exchange
        self.final_exchange = final_exchange
        self.calendar = calendar
        self.payment_convention = payment_convention
        self.is_in_arrears = is_in_arrears
        self.fixing_days = fixing_days

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        """Parse and convert string inputs to appropriate types."""
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.start_date = dateParser.parse_date(self.start_date)
        self.end_date = dateParser.parse_date(self.end_date)

        # Parse leg 1
        self.currency1 = self.currency1.upper()
        self.notional1 = float(self.notional1)
        self.spread1 = float(self.spread1)

        # Parse leg 2
        self.currency2 = self.currency2.upper()
        self.notional2 = float(self.notional2)
        self.spread2 = float(self.spread2)

        # Parse common parameters
        self.fixing_days = int(self.fixing_days)

        # Parse boolean flags
        if isinstance(self.initial_exchange, str):
            self.initial_exchange = self.initial_exchange.lower() in ('true', 'yes', '1')
        else:
            self.initial_exchange = bool(self.initial_exchange)

        if isinstance(self.final_exchange, str):
            self.final_exchange = self.final_exchange.lower() in ('true', 'yes', '1')
        else:
            self.final_exchange = bool(self.final_exchange)

        if isinstance(self.is_in_arrears, str):
            self.is_in_arrears = self.is_in_arrears.lower() in ('true', 'yes', '1')
        else:
            self.is_in_arrears = bool(self.is_in_arrears)

    def _validate_input(self):
        """Validate trade parameters."""
        if self.notional1 <= 0:
            raise ValueError("Notional1 must be positive")

        if self.notional2 <= 0:
            raise ValueError("Notional2 must be positive")

        if self.start_date >= self.end_date:
            raise ValueError("End date must be after start date")

        if self.start_date < self.evaluation_date:
            raise ValueError("Start date cannot be before evaluation date")

        if self.currency1 == self.currency2:
            raise ValueError("Leg currencies must be different for a cross-currency swap")

        if self.fixing_days < 0:
            raise ValueError("Fixing days must be non-negative")

    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with Cross-Currency Swap trade data for ORE.

        Returns:
            tuple: ('Swap', pd.DataFrame with trade parameters)

        Note: CCS is represented as a Swap with two floating legs in different currencies.
        """
        trade_df = pd.DataFrame({
            'TradeId': [self.__name__],
            'TradeType': [self.__name__],
            'CounterParty': ['CPTY_A'],
            'StartDate': [dateParser.ql2pydate(self.start_date).strftime('%Y-%m-%d')],
            'EndDate': [dateParser.ql2pydate(self.end_date).strftime('%Y-%m-%d')],
            'Calendar': [self.calendar],
            'PaymentConvention': [self.payment_convention],
            'IsInArrears': [str(self.is_in_arrears).lower()],
            'FixingDays': [self.fixing_days],

            # Leg 1 parameters
            'Currency1': [self.currency1],
            'Notional1': [self.notional1],
            'Index1': [self.index1],
            'Spread1': [self.spread1],
            'Tenor1': [self.tenor1],
            'DayCounter1': [self.day_counter1],

            # Leg 2 parameters
            'Currency2': [self.currency2],
            'Notional2': [self.notional2],
            'Index2': [self.index2],
            'Spread2': [self.spread2],
            'Tenor2': [self.tenor2],
            'DayCounter2': [self.day_counter2],

            # Exchange flags
            'InitialExchange': [str(self.initial_exchange).lower()],
            'FinalExchange': [str(self.final_exchange).lower()],
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
