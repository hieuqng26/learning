"""
OREPortfolio - Portfolio class for ORE-based trade pricing.

This class provides portfolio-level pricing functionality for multiple trades
using the Open Risk Engine (ORE).
"""

from typing import Dict, Optional, Any
import pandas as pd
import project.qld.engine.parser.date as dateParser
from project.orelab import ORERunner
from project.orelab.trade_builders import TradeBuilders


class OREPortfolio:
    """
    Portfolio class for pricing multiple trades using ORE (Open Risk Engine).

    This class provides functionality for:
    - Accepting trade data as DataFrames (similar to Excel sheet input)
    - Running ORE pricing and exposure calculations for all trades
    - Aggregating results (NPV, CVA, DVA, exposures) at portfolio level

    Usage:
        # Create portfolio with trade DataFrames
        trades = {
            'InterestRateSwap': swap_df,
            'FxForward': fxfwd_df
        }
        netting_df = pd.DataFrame({...})

        portfolio = OREPortfolio(
            evaluation_date='2016-02-05',
            trades=trades,
            netting_sets=netting_df
        )

        # Price all trades
        portfolio.price()

        # Access results
        print(portfolio.result['npv'])  # Portfolio NPV
        print(portfolio.result['trades'])  # Individual trade results
    """

    def __init__(
        self,
        evaluation_date: str,
        trades: Dict[str, pd.DataFrame],
        netting_sets: Optional[pd.DataFrame] = None
    ):
        """
        Initialize OREPortfolio.

        Args:
            evaluation_date: The date at which trades will be valued (YYYY-MM-DD)
            trades: Dictionary mapping trade type to DataFrame with trade data.
                    Keys should be ORE trade types (e.g., 'InterestRateSwap', 'FxForward')
                    Values are DataFrames with one row per trade
            netting_sets: Optional DataFrame with netting set configuration.
                         Columns: NettingSetId, CounterParty, CSAThreshold, CSAMta, CollateralCurrency

        Example:
            trades = {
                'InterestRateSwap': pd.DataFrame({
                    'TradeId': ['Swap_1', 'Swap_2'],
                    'TradeType': ['InterestRateSwap', 'InterestRateSwap'],
                    ...
                }),
                'FxForward': pd.DataFrame({
                    'TradeId': ['FxFwd_1'],
                    'TradeType': ['FxForward'],
                    ...
                })
            }
        """
        self.evaluation_date = evaluation_date
        self.trades = trades
        self.netting_sets = netting_sets
        self.result = {}

        # Validate inputs
        self._validate_inputs()

    def _validate_inputs(self):
        """
        Validate inputs.

        Raises:
            ValueError
        """
        if not self.trades:
            raise ValueError("trades dictionary cannot be empty")

        for trade_type, df in self.trades.items():
            if trade_type not in TradeBuilders:
                raise ValueError(
                    f"Unknown trade type: {trade_type}. "
                    f"Supported types: {list(TradeBuilders.keys())}"
                )

            if df is None or df.empty:
                raise ValueError(f"DataFrame for {trade_type} is empty")

            # Validate TradeId uniqueness across all trades
            if 'TradeId' in df.columns:
                if df['TradeId'].duplicated().any():
                    raise ValueError(f"Duplicate TradeIds found in {trade_type}")

    def _build_default_netting(self):
        """
        Build default netting set DataFrame if none provided.

        Returns:
            pd.DataFrame: Default netting set configuration
        """
        return pd.DataFrame({
            'NettingSetId': ['CPTY_A'],
            'CounterParty': ['CPTY_A'],
            'CSAThreshold': [0],
            'CSAMta': [0],
            'CollateralCurrency': ['EUR']
        })

    def price(
        self,
        sensitivity_config: Optional[Dict[str, Any]] = None,
        scenario_config: Optional[Dict[str, Any]] = None,
        cleanup: bool = True
    ):
        """
        Price all trades in the portfolio using ORE.

        This method:
        1. Prepares inputs for ORERunner
        2. Runs ORE analytics for all trades
        3. Extracts and aggregates results

        Args:
            sensitivity_config: Optional dict with sensitivity analysis configuration.
                See OREBaseTrade.build_sensitivity_config() for format.
            scenario_config: Optional dict with stress scenario configuration.
            cleanup: Whether to cleanup temporary files after execution (default: True)

        Stores in self.result with trade/nettingset/portfolio levels:
            Structure:
            {
                'base': {
                    'npv': {'trade': DataFrame, 'nettingset': None, 'portfolio': float},
                    'cva': {'trade': None, 'nettingset': None, 'portfolio': float},
                    'dva': {'trade': None, 'nettingset': None, 'portfolio': float},
                    'exposures': {'trade': DataFrame, 'nettingset': DataFrame, 'portfolio': DataFrame}
                },
                'sensitivity': {
                    'npv': {'trade': DataFrame, 'nettingset': None, 'portfolio': None},
                    'cva': {'trade': None, 'nettingset': None, 'portfolio': None},
                    'dva': {'trade': None, 'nettingset': None, 'portfolio': None},
                    'exposures': {'trade': DataFrame, 'nettingset': DataFrame, 'portfolio': DataFrame}
                },
                'stress': {
                    'npv': {'trade': DataFrame, 'nettingset': None, 'portfolio': None},
                    'cva': {'trade': None, 'nettingset': None, 'portfolio': None},
                    'dva': {'trade': None, 'nettingset': None, 'portfolio': None},
                    'exposures': {'trade': DataFrame, 'nettingset': DataFrame, 'portfolio': DataFrame}
                }
            }
        """
        # Prepare netting sets
        netting_df = self.netting_sets if self.netting_sets is not None else self._build_default_netting()

        # Prepare inputs for ORERunner
        inputs = {
            'trades': self.trades,
            'netting_sets': netting_df
        }

        # Convert evaluation date to string format YYYY-MM-DD
        if hasattr(self.evaluation_date, 'year'):
            # QuantLib date
            asof_date_str = dateParser.ql2pydate(self.evaluation_date).strftime('%Y-%m-%d')
        else:
            # Already string
            asof_date_str = self.evaluation_date

        # Run ORE analytics
        with ORERunner(
            inputs,
            asof_date=asof_date_str,
            cleanup=cleanup,
            sensitivity_config=sensitivity_config,
            scenario_config=scenario_config
        ) as runner:
            runner.run()

            # Get NPV results
            npv_df = runner.get_npv()
            npv_sensitivity_df = runner.get_sensitivity()
            npv_stress_df = runner.get_stress()

            # Get exposure results at different levels
            exposures = runner.get_exposures()
            exposures_sensitivity = runner.get_xva_sensitivity_exposures()
            exposures_stress = runner.get_xva_stress_exposures()

            # Get XVA for CVA/DVA
            xva_df = runner.get_xva()

            # Build structured results with trade/nettingset/portfolio levels
            self.result = self._build_structured_results(
                npv_df,
                npv_sensitivity_df,
                npv_stress_df,
                exposures,
                exposures_sensitivity,
                exposures_stress,
                xva_df
            )

    def get_trade_ids(self):
        """
        Get all trade IDs in the portfolio.

        Returns:
            list: List of all TradeIds across all trade types
        """
        trade_ids = []
        for df in self.trades.values():
            if 'TradeId' in df.columns:
                trade_ids.extend(df['TradeId'].tolist())
        return trade_ids

    def get_trade_count(self):
        """
        Get total number of trades in the portfolio.

        Returns:
            int: Total trade count
        """
        return sum(len(df) for df in self.trades.values())

    def _build_structured_results(
        self,
        npv_df,
        npv_sensitivity_df,
        npv_stress_df,
        exposures,
        exposures_sensitivity,
        exposures_stress,
        xva_df
    ):
        """
        Build structured results with trade/nettingset/portfolio levels.

        Returns:
            dict: Structured results with base/sensitivity/stress sections
        """
        # Aggregate exposures to portfolio level
        exposures_portfolio = self._aggregate_exposures_to_portfolio(
            exposures['trade'],
            by=['Date', 'Time']
        )
        exposures_sensitivity_portfolio = self._aggregate_exposures_to_portfolio(
            exposures_sensitivity['trade'],
            by=['Type', 'Factor_1', 'ShiftSize_1', 'Factor_2', 'ShiftSize_2',
                'Currency', 'Date', 'Time']
        )
        exposures_stress_portfolio = self._aggregate_exposures_to_portfolio(
            exposures_stress['trade'],
            by=['Scenario', 'Date', 'Time']
        )

        # Build structured result
        result = {
            'base': {
                'npv': npv_df,
                'exposures': {
                    'trade': exposures['trade'],
                    'nettingset': exposures['nettingset'],
                    'portfolio': exposures_portfolio
                }
            },
            'sensitivity': {
                'npv': npv_sensitivity_df,
                'exposures': {
                    'trade': exposures_sensitivity['trade'],
                    'nettingset': exposures_sensitivity['nettingset'],
                    'portfolio': exposures_sensitivity_portfolio
                }
            },
            'stress': {
                'npv': npv_stress_df,
                'exposures': {
                    'trade': exposures_stress['trade'],
                    'nettingset': exposures_stress['nettingset'],
                    'portfolio': exposures_stress_portfolio
                }
            }
        }

        return result

    def _aggregate_exposures_to_portfolio(self, exposure_df, by: list) -> Optional[pd.DataFrame]:
        """
        Aggregate exposures to portfolio level by date.

        Args:
            exposure_df: DataFrame with trade or nettingset level exposures

        Returns:
            pd.DataFrame: Portfolio-level aggregated exposures by date
        """
        if exposure_df is None or exposure_df.empty:
            return None

        exposure_df[by] = exposure_df[by].fillna('')
        portfolio_df = exposure_df.groupby(by)[[
            'EPE', 'ENE', 'AllocatedEPE',
            'AllocatedENE', 'PFE', 'BaselEE', 'BaselEEE',
            'TimeWeightedBaselEPE', 'TimeWeightedBaselEEPE'
        ]].sum().reset_index()

        # Aggregate base exposures
        # base_exposure = exposure_df[exposure_df['Type'] == 'Base'][['Date', 'EPE', 'ENE']]
        # base_exposure = base_exposure.groupby('Date').sum().reset_index()

        # # Aggregate exposures by factor and type
        # for factor in exposure_df['Factor_1'].dropna().unique():
        #     # Filter for relevant factors only
        #     if not any(x in factor for x in ['DiscountCurve', 'FXSpot', 'FXVolatility']):
        #         continue

        #     for _type in exposure_df['Type'].dropna().unique():
        #         if _type == 'Base':
        #             continue
        #         factor_exposure = exposure_df[
        #             exposure_df['Factor_1'].eq(factor) &
        #             exposure_df['Type'].eq(_type)
        #         ][['Date', 'EPE', 'ENE']]
        #         factor_exposure = factor_exposure.groupby('Date').sum().reset_index()
        #         factor_exposure = factor_exposure.rename(
        #             columns={
        #                 'EPE': f'EPE|{factor}|{_type}',
        #                 'ENE': f'ENE|{factor}|{_type}'
        #             }
        #         )
        #         base_exposure = pd.merge(base_exposure, factor_exposure, on='Date', how='left')

        return portfolio_df.reset_index(drop=True)
