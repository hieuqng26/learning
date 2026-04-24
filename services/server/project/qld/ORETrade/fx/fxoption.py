"""
FX Option Trade Implementation using ORE.

This module provides FX Vanilla Option pricing using the Open Risk Engine (ORE).
"""

import pandas as pd
import project.qld.engine.parser.date as dateParser

from ..ore_base_trade import OREBaseTrade


class FXOption(OREBaseTrade):
    """
    FX Vanilla Option trade priced using ORE.

    An FX Option gives the holder the right (but not obligation) to exchange
    one currency for another at a future date at a predetermined exchange rate.
    """

    __name__ = "FxOption"

    def __init__(self, evaluation_date, bought_currency, bought_amount, sold_currency, sold_amount,
                 long_short, option_type, style, exercise_date, settlement='Cash',
                 payoff_at_expiry=False, premium_amount=None, premium_currency=None,
                 premium_pay_date=None):
        """
        Initialize FX Option trade.

        Args:
            evaluation_date: Valuation date
            bought_currency: Currency to buy (e.g., 'EUR')
            bought_amount: Amount to buy
            sold_currency: Currency to sell (e.g., 'USD')
            sold_amount: Amount to sell (strike in foreign currency units)
            long_short: 'Long' or 'Short' position
            option_type: 'Call' or 'Put'
            style: 'European' or 'American'
            exercise_date: Exercise date(s) - single date string or list of date strings
            settlement: 'Cash' or 'Physical' (default: 'Cash')
            payoff_at_expiry: Whether payoff is at expiry (default: False)
            premium_amount: Option premium amount(s) - single value or list (optional)
            premium_currency: Currency of premium(s) - single value or list (optional)
            premium_pay_date: Premium payment date(s) - single date or list (optional)
        """
        super().__init__(evaluation_date)

        self.bought_currency = bought_currency
        self.bought_amount = bought_amount
        self.sold_currency = sold_currency
        self.sold_amount = sold_amount
        self.long_short = long_short
        self.option_type = option_type
        self.style = style
        self.exercise_date = exercise_date  # Can be single date or list
        self.settlement = settlement
        self.payoff_at_expiry = payoff_at_expiry
        self.premium_amount = premium_amount  # Can be single value or list
        self.premium_currency = premium_currency  # Can be single value or list
        self.premium_pay_date = premium_pay_date  # Can be single date or list

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        """Parse and convert string inputs to appropriate types."""
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.bought_currency = self.bought_currency.upper()
        self.sold_currency = self.sold_currency.upper()
        self.bought_amount = float(self.bought_amount)
        self.sold_amount = float(self.sold_amount)

        # Parse exercise date(s) - handle both single date and list of dates
        if isinstance(self.exercise_date, list):
            self.exercise_date = [dateParser.parse_date(date) for date in self.exercise_date]
        else:
            self.exercise_date = dateParser.parse_date(self.exercise_date)

        # Validate and normalize enum values
        self.long_short = str(self.long_short).capitalize()
        self.option_type = str(self.option_type).capitalize()
        self.style = str(self.style).capitalize()
        self.settlement = str(self.settlement).capitalize()

        # Parse payoff_at_expiry to boolean
        if isinstance(self.payoff_at_expiry, str):
            self.payoff_at_expiry = self.payoff_at_expiry.lower() in ('true', 'yes', '1')
        else:
            self.payoff_at_expiry = bool(self.payoff_at_expiry)

        # Parse premium data if provided - handle both single and multiple premiums
        if self.premium_amount is not None:
            if isinstance(self.premium_amount, list):
                self.premium_amount = [float(amt) for amt in self.premium_amount]
            else:
                self.premium_amount = float(self.premium_amount)

        if self.premium_currency is not None:
            if isinstance(self.premium_currency, list):
                self.premium_currency = [ccy.upper() for ccy in self.premium_currency]
            else:
                self.premium_currency = self.premium_currency.upper()

        if self.premium_pay_date is not None:
            if isinstance(self.premium_pay_date, list):
                self.premium_pay_date = [dateParser.parse_date(date) for date in self.premium_pay_date]
            else:
                self.premium_pay_date = dateParser.parse_date(self.premium_pay_date)

    def _validate_input(self):
        """Validate trade parameters."""
        if self.bought_amount <= 0:
            raise ValueError("Bought amount must be positive")

        if self.sold_amount <= 0:
            raise ValueError("Sold amount must be positive")

        # Validate exercise date(s) - handle both single and multiple dates
        if isinstance(self.exercise_date, list):
            for date in self.exercise_date:
                if date <= self.evaluation_date:
                    raise ValueError("All exercise dates must be after evaluation date")
        else:
            if self.exercise_date <= self.evaluation_date:
                raise ValueError("Exercise date must be after evaluation date")

        if self.bought_currency == self.sold_currency:
            raise ValueError("Bought and sold currencies must be different")

        if self.long_short not in ('Long', 'Short'):
            raise ValueError("Long/Short must be 'Long' or 'Short'")

        if self.option_type not in ('Call', 'Put'):
            raise ValueError("Option type must be 'Call' or 'Put'")

        if self.style not in ('European', 'American'):
            raise ValueError("Style must be 'European' or 'American'")

        if self.settlement not in ('Cash', 'Physical'):
            raise ValueError("Settlement must be 'Cash' or 'Physical'")

        # Validate premium data if partially provided
        if self.premium_amount is not None:
            if self.premium_currency is None or self.premium_pay_date is None:
                raise ValueError("If premium_amount is provided, premium_currency and premium_pay_date must also be provided")

            # If premiums are lists, validate they have the same length
            if isinstance(self.premium_amount, list):
                if not isinstance(self.premium_currency, list) or not isinstance(self.premium_pay_date, list):
                    raise ValueError("If premium_amount is a list, premium_currency and premium_pay_date must also be lists")
                if not (len(self.premium_amount) == len(self.premium_currency) == len(self.premium_pay_date)):
                    raise ValueError("premium_amount, premium_currency, and premium_pay_date lists must have the same length")

    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with FX Option trade data for ORE.

        Returns:
            tuple: ('FxOption', pd.DataFrame with trade parameters)
        """
        # Format exercise date(s)
        if isinstance(self.exercise_date, list):
            exercise_dates = [dateParser.ql2pydate(date).strftime('%Y-%m-%d') for date in self.exercise_date]
        else:
            exercise_dates = dateParser.ql2pydate(self.exercise_date).strftime('%Y-%m-%d')

        trade_df = pd.DataFrame({
            'TradeId': [self.__name__],
            'TradeType': [self.__name__],
            'CounterParty': ['CPTY_A'],
            'LongShort': [self.long_short],
            'OptionType': [self.option_type],
            'Style': [self.style],
            'Settlement': [self.settlement],
            'PayOffAtExpiry': [str(self.payoff_at_expiry).lower()],
            'ExerciseDate': [exercise_dates],  # Can be single date or list
            'BoughtCurrency': [self.bought_currency],
            'BoughtAmount': [self.bought_amount],
            'SoldCurrency': [self.sold_currency],
            'SoldAmount': [self.sold_amount],
        })

        # Add premium data if provided
        if self.premium_amount is not None:
            # Format premium dates
            if isinstance(self.premium_pay_date, list):
                premium_dates = [dateParser.ql2pydate(date).strftime('%Y-%m-%d') for date in self.premium_pay_date]
            else:
                premium_dates = dateParser.ql2pydate(self.premium_pay_date).strftime('%Y-%m-%d')

            trade_df['PremiumAmount'] = [self.premium_amount]  # Can be single value or list
            trade_df['PremiumCurrency'] = [self.premium_currency]  # Can be single value or list
            trade_df['PremiumPayDate'] = [premium_dates]  # Can be single date or list

        return (self.__name__, trade_df)

    def _filter_epe_dates(self, exposure_df):
        """
        Filter exposure DataFrame to include only relevant dates.

        Args:
            exposure_df (pd.DataFrame): DataFrame with exposure data including 'Date' column.
        Returns:
            pd.DataFrame: Filtered DataFrame.
        """
        try:
            if isinstance(self.exercise_date, list):
                exercise_date = max(self.exercise_date)
            else:
                exercise_date = self.exercise_date
            exposure_df['Date'] = pd.to_datetime(exposure_df['Date'])
            start_date = dateParser.ql2npdate(self.evaluation_date)
            end_date = dateParser.ql2npdate(exercise_date)
            filtered_df = exposure_df[(exposure_df['Date'] >= start_date) & (exposure_df['Date'] <= end_date)]
        except Exception as e:
            pass  # In case of error, return unfiltered DataFrame
        return filtered_df
