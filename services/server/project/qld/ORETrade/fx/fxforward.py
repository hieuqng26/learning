"""
FX Forward Trade Implementation using ORE.

This module provides FX Forward pricing using the Open Risk Engine (ORE).
"""

import pandas as pd
import project.qld.engine.parser.date as dateParser

from ...ORETrade.ore_base_trade import OREBaseTrade


class FXForward(OREBaseTrade):
    """
    FX Forward trade priced using ORE.

    An FX Forward is an agreement to exchange one currency for another
    at a future date at a predetermined rate.
    """

    __name__ = "FxForward"

    def __init__(self, evaluation_date, value_date, bought_currency, bought_amount,
                 sold_currency, sold_amount, settlement='Physical',
                 settlement_currency=None, fx_index=None, settlement_date=None,
                 payment_lag=None, payment_calendar=None, payment_convention=None):
        """
        Initialize FX Forward trade.

        Args:
            evaluation_date: Valuation date
            value_date: Value date for the FX forward
            bought_currency: Currency being bought (e.g., 'EUR')
            bought_amount: Amount of bought currency
            sold_currency: Currency being sold (e.g., 'USD')
            sold_amount: Amount of sold currency
            settlement: Settlement type - 'Physical' or 'Cash' (default: 'Physical')

            Cash settlement parameters (optional, only for settlement='Cash'):
            settlement_currency: Currency for cash settlement
            fx_index: FX index for cash settlement (e.g., 'FX-TR20H-EUR-USD')
            settlement_date: Settlement date for cash settlement
            payment_lag: Payment lag (e.g., '2D')
            payment_calendar: Payment calendar (e.g., 'USD')
            payment_convention: Payment convention (e.g., 'Following')
        """
        super().__init__(evaluation_date)

        self.value_date = value_date
        self.bought_currency = bought_currency
        self.bought_amount = bought_amount
        self.sold_currency = sold_currency
        self.sold_amount = sold_amount
        self.settlement = settlement

        # Settlement data (for cash settlement)
        self.settlement_currency = settlement_currency
        self.fx_index = fx_index
        self.settlement_date = settlement_date
        self.payment_lag = payment_lag
        self.payment_calendar = payment_calendar
        self.payment_convention = payment_convention

        self._parse_input()
        self._validate_input()

    def _parse_input(self):
        """Parse and convert string inputs to appropriate types."""
        self.evaluation_date = dateParser.parse_date(self.evaluation_date)
        self.value_date = dateParser.parse_date(self.value_date)
        self.bought_currency = self.bought_currency.upper()
        self.sold_currency = self.sold_currency.upper()
        self.bought_amount = float(self.bought_amount)
        self.sold_amount = float(self.sold_amount)

        # Parse settlement type
        if isinstance(self.settlement, str):
            self.settlement = self.settlement.capitalize()

        # Parse optional settlement data
        if self.settlement_currency:
            self.settlement_currency = self.settlement_currency.upper()
        if self.settlement_date:
            self.settlement_date = dateParser.parse_date(self.settlement_date)

    def _validate_input(self):
        """Validate trade parameters."""
        if self.bought_amount <= 0:
            raise ValueError("Bought amount must be positive")

        if self.sold_amount <= 0:
            raise ValueError("Sold amount must be positive")

        if self.value_date <= self.evaluation_date:
            raise ValueError("Value date must be after evaluation date")

        if self.bought_currency == self.sold_currency:
            raise ValueError("Bought and sold currencies must be different")

        if self.settlement not in ('Physical', 'Cash'):
            raise ValueError("Settlement must be 'Physical' or 'Cash'")

        # Validate cash settlement parameters
        if self.settlement == 'Cash':
            if not self.settlement_currency:
                raise ValueError("Settlement currency is required for cash settlement")
            if not self.fx_index:
                raise ValueError("FX index is required for cash settlement")

    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with FX Forward trade data for ORE.

        Returns:
            tuple: ('FxForward', pd.DataFrame with trade parameters)
        """
        data = {
            'TradeId': [self.__name__],
            'TradeType': [self.__name__],
            'CounterParty': ['CPTY_A'],
            'ValueDate': [dateParser.ql2pydate(self.value_date).strftime('%Y-%m-%d')],
            'BoughtCurrency': [self.bought_currency],
            'BoughtAmount': [self.bought_amount],
            'SoldCurrency': [self.sold_currency],
            'SoldAmount': [self.sold_amount],
            'Settlement': [self.settlement],
        }

        # Add settlement data if cash settlement
        if self.settlement == 'Cash':
            data['SettlementCurrency'] = [self.settlement_currency]
            data['FXIndex'] = [self.fx_index]

            if self.settlement_date:
                data['SettlementDate'] = [dateParser.ql2pydate(self.settlement_date).strftime('%Y-%m-%d')]

            if self.payment_lag:
                data['PaymentLag'] = [self.payment_lag]

            if self.payment_calendar:
                data['PaymentCalendar'] = [self.payment_calendar]

            if self.payment_convention:
                data['PaymentConvention'] = [self.payment_convention]

        trade_df = pd.DataFrame(data)
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
        start_date = dateParser.ql2npdate(self.evaluation_date)
        end_date = dateParser.ql2npdate(self.settlement_date)
        filtered_df = exposure_df[(exposure_df['Date'] >= start_date) & (exposure_df['Date'] <= end_date)]
        return filtered_df
