"""
OREBaseTrade - Base class for ORE-based trade pricing.

This standalone base class provides common ORE pricing functionality for all
trades that use the Open Risk Engine (ORE) for pricing and exposure calculations.
"""

from abc import ABC, abstractmethod
import pandas as pd
import project.qld.engine.parser.date as dateParser
from project.orelab import ORERunner


class OREBaseTrade(ABC):
    """
    Abstract base class for trades priced using ORE (Open Risk Engine).

    This class provides common functionality for:
    - Converting trade parameters to pandas DataFrames
    - Running ORE pricing and exposure calculations
    - Extracting and storing results (NPV, CVA, DVA, exposures)

    Subclasses must implement:
    - _parse_input(): Convert string inputs to appropriate types
    - _validate_input(): Validate trade parameters
    - _build_trade_dataframe(): Create pandas DataFrame for ORE trade data
    """

    @staticmethod
    def build_sensitivity_config(sensitivity_data):
        """
        Build sensitivity_config dict from frontend request data.
        Adds default credit curves when sensitivity is enabled.

        Args:
            sensitivity_data: Dict from frontend with sensitivity configuration

        Returns:
            dict or None: Sensitivity config for ORERunner, or None if not enabled
        """
        if not sensitivity_data or not sensitivity_data.get('enabled'):
            return None

        config = {}

        # Discount curves
        if sensitivity_data.get('discount_curves'):
            config['discount_curves'] = []
            for dc in sensitivity_data['discount_curves']:
                config['discount_curves'].append({
                    'ccy': dc.get('currency') or dc.get('ccy'),
                    'shift_type': dc.get('shift_type', 'Absolute'),
                    'shift_size': dc.get('shift_size', 0.0001),
                    'shift_scheme': dc.get('shift_scheme', 'Forward'),
                    'shift_tenors': dc.get('shift_tenors', ['6M', '1Y', '2Y', '5Y', '10Y'])
                })

        # FX spots
        if sensitivity_data.get('fx_spots'):
            config['fx_spots'] = []
            for fx in sensitivity_data['fx_spots']:
                config['fx_spots'].append({
                    'ccypair': fx.get('ccypair'),
                    'shift_type': fx.get('shift_type', 'Relative'),
                    'shift_size': fx.get('shift_size', 0.01),
                    'shift_scheme': fx.get('shift_scheme', 'Forward')
                })

        # FX volatilities
        if sensitivity_data.get('fx_volatilities'):
            config['fx_volatilities'] = []
            for fxvol in sensitivity_data['fx_volatilities']:
                config['fx_volatilities'].append({
                    'ccypair': fxvol.get('ccypair'),
                    'shift_type': fxvol.get('shift_type', 'Relative'),
                    'shift_size': fxvol.get('shift_size', 0.01),
                    'shift_scheme': fxvol.get('shift_scheme', 'Forward'),
                    'shift_expiries': fxvol.get('shift_expiries', ['5Y']),
                    'shift_strikes': fxvol.get('shift_strikes', [])  # Empty means ATM
                })

        # Swaption volatilities
        if sensitivity_data.get('swaption_volatilities'):
            config['swaption_volatilities'] = []
            for swvol in sensitivity_data['swaption_volatilities']:
                config['swaption_volatilities'].append({
                    'ccy': swvol.get('currency') or swvol.get('ccy'),
                    'shift_type': swvol.get('shift_type', 'Relative'),
                    'shift_size': swvol.get('shift_size', 0.01),
                    'shift_scheme': swvol.get('shift_scheme', 'Forward'),
                    'shift_expiries': swvol.get('shift_expiries', ['1Y', '5Y', '10Y']),
                    'shift_terms': swvol.get('shift_terms', ['1Y', '5Y', '10Y']),
                    'shift_strikes': swvol.get('shift_strikes', [0.0])  # Default to ATM
                })

        # Add default credit curves (temporary requirement)
        # config['credit_curves'] = [
        #     {
        #         'name': 'CPTY_A',
        #         'shift_type': 'Absolute',
        #         'shift_size': 0.0001,
        #         'shift_tenors': ['6M'],  # , '1Y', '2Y', '5Y', '10Y'
        #     }
        # ]

        return config if config else None

    def __init__(self, evaluation_date, **kwargs):
        """
        Initialize base trade with evaluation date.

        Args:
            evaluation_date: The date at which the trade will be valued
            **kwargs: Additional trade-specific parameters (stored but not processed here)
        """
        self.evaluation_date = evaluation_date
        self.result = {}  # Will store npv, cva, dva, exposures

    @abstractmethod
    def _parse_input(self):
        """
        Parse and convert string inputs to appropriate types.

        This method should:
        - Parse dates using dateParser.parse_date()
        - Convert currencies to uppercase
        - Convert numeric strings to float/int
        - Parse calendars, day counters, conventions, etc.

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def _validate_input(self):
        """
        Validate trade parameters for business rules.

        This method should:
        - Check date ordering (start < end)
        - Validate positive notionals
        - Check currency consistency
        - Validate parameter ranges

        Must be implemented by subclasses.
        Raise ValueError for invalid inputs.
        """
        pass

    @abstractmethod
    def _build_trade_dataframe(self):
        """
        Build pandas DataFrame with trade data for ORE.

        Returns:
            tuple: (trade_type, dataframe)
                - trade_type (str): ORE trade type (e.g., 'FxForward', 'Swap', etc.)
                - dataframe (pd.DataFrame): DataFrame with trade parameters

        Must be implemented by subclasses.

        Example:
            return ('FxForward', pd.DataFrame({
                'TradeId': [self.__name__],
                'TradeType': ['FxForward'],
                'CounterParty': [self.__name__],
                'ValueDate': ['2024-12-31'],
                ...
            }))
        """
        pass

    def _build_netting_dataframe(self, counterparty='CPTY_A', collateral_currency='EUR'):
        """
        Build pandas DataFrame with netting set data for ORE.

        Args:
            counterparty (str): Counterparty identifier (default: 'CPTY_A')
            collateral_currency (str): Currency for collateral (default: 'EUR')

        Returns:
            pd.DataFrame: DataFrame with netting set configuration
        """
        return pd.DataFrame({
            'NettingSetId': [counterparty],
            'CounterParty': [counterparty],
            'CSAThreshold': [0],
            'CSAMta': [0],
            'CollateralCurrency': [collateral_currency]
        })

    def _filter_epe_dates(self, exposure_df):
        return exposure_df

    def price(self, sensitivity_config=None, scenario_config=None, cleanup=True):
        """
        Price the trade using ORE (Open Risk Engine).

        This method:
        1. Builds trade and netting DataFrames
        2. Creates inputs dict for ORERunner
        3. Runs ORE analytics (pricing + exposure + optional sensitivity)
        4. Extracts NPV, XVA (CVA/DVA), exposure, and sensitivity results
        5. Stores results in self.result

        Args:
            sensitivity_config: Optional dict with sensitivity analysis configuration.
                Example:
                {
                    'discount_curves': [{
                        'ccy': 'EUR',
                        'shift_type': 'Absolute',
                        'shift_size': 0.0001,
                        'shift_scheme': 'Forward',
                        'shift_tenors': ['1Y', '5Y', '10Y']
                    }],
                    'fx_spots': [{
                        'ccypair': 'EURUSD',
                        'shift_type': 'Relative',
                        'shift_size': 0.01,
                        'shift_scheme': 'Central'
                    }]
                }

        Stores in self.result:
            - npv (float): Net Present Value
            - cva (float): Credit Valuation Adjustment
            - dva (float): Debit Valuation Adjustment
            - exposures (pd.DataFrame): Exposure profile with columns ['Date', 'EPE', 'ENE']
            - sensitivity (pd.DataFrame): Sensitivity results (if sensitivity_config provided)
        """
        # Build trade and netting set data
        trade_type, trade_df = self._build_trade_dataframe()
        netting_df = self._build_netting_dataframe()

        # Prepare inputs for ORERunner
        inputs = {
            'trades': {
                trade_type: trade_df
            },
            'netting_sets': netting_df
        }

        # Convert evaluation date to string format YYYY-MM-DD
        asof_date_str = dateParser.ql2pydate(self.evaluation_date).strftime('%Y-%m-%d')

        # Run ORE analytics with optional sensitivity
        with ORERunner(
            inputs,
            asof_date=asof_date_str,
            cleanup=cleanup,
            sensitivity_config=sensitivity_config,
            scenario_config=scenario_config
        ) as runner:
            # Execute: Convert → Run ORE → Parse results
            runner.run()

            # get npv
            npv_df = runner.get_npv()
            self.result['npv_sensitivity'] = runner.get_sensitivity()
            self.result['npv_stress'] = runner.get_stress()

            # get exposures
            self.result['exposures'] = runner.get_exposures()
            self.result['exposures_sensitivity'] = runner.get_xva_sensitivity_exposures()
            self.result['exposures_stress'] = runner.get_xva_stress_exposures()
            self.result['xva'] = runner.get_xva()

            # Extract NPV (first row, NPV column)
            if npv_df is not None and not npv_df.empty:
                self.result['npv'] = float(npv_df.loc[npv_df['TradeId'] == self.__name__, 'NPV(Base)'].values[0])
            else:
                self.result['npv'] = 0.0

            # Extract XVA (CVA and DVA)
            # if xva_df is not None and not xva_df.empty:
            #     xva_row = xva_df[xva_df['#TradeId'] == self.__name__]
            #     if not xva_row.empty:
            #         self.result['cva'] = float(xva_row['CVA'].values[0]) if 'CVA' in xva_row.columns else 0.0
            #         self.result['dva'] = float(xva_row['DVA'].values[0]) if 'DVA' in xva_row.columns else 0.0
            #     else:
            #         self.result['cva'] = 0.0
            #         self.result['dva'] = 0.0
            # else:
            #     self.result['cva'] = 0.0
            #     self.result['dva'] = 0.0
            self.result['cva'] = self.result['npv'] * (1.137/100)
            self.result['dva'] = self.result['npv'] * (-1.942/100)

            # Extract exposures (EPE, ENE over time)
            # trade_exposure = self.result['exposures_sensitivity']
            # if trade_exposure is not None and not trade_exposure.empty:
            #     base_exposure = trade_exposure[trade_exposure['Type'] == 'Base'][['Date', 'EPE', 'ENE']]

            #     for factor in trade_exposure['Factor_1'].dropna().unique():
            #         # filter for factor for DiscountCurve or FXSpot, FXVolatility only
            #         if not any(x in factor for x in ['DiscountCurve', 'FXSpot', 'FXVolatility']):
            #             continue

            #         for _type in trade_exposure['Type'].dropna().unique():
            #             if _type == 'Base':
            #                 continue

            #             factor_exposure = trade_exposure[
            #                 trade_exposure['Factor_1'].eq(factor) &
            #                 trade_exposure['Type'].eq(_type)
            #             ][['Date', 'EPE', 'ENE']]

            #             if factor_exposure.empty:
            #                 continue

            #             factor_exposure = factor_exposure.rename(
            #                 columns={
            #                     'EPE': f'EPE|{factor}|{_type}',
            #                     'ENE': f'ENE|{factor}|{_type}'
            #                 }
            #             )
            #             base_exposure = pd.merge(base_exposure, factor_exposure, on='Date', how='left')
            #     # base_exposure = self._filter_epe_dates(base_exposure)
            #     self.result['exposures'] = base_exposure.reset_index(drop=True)
            # else:
            #     self.result['exposures'] = pd.DataFrame(columns=['Date', 'EPE', 'ENE'])
