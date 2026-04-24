import os
import pandas as pd
import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging

from project.qld.engine.utils.market import marketTools
from project.qld.engine.utils.pricing import riskConfiguration as riskconf

MARKET_DATA_PATH = Path("project/data/db")
logger = logging.getLogger(__name__)


class Portfolio:
    """Portfolio class for pricing multiple trades of the same type in parallel.

    This class provides efficient batch pricing by:
    1. Loading market data once and sharing across all trades
    2. Executing trade pricing in parallel using ThreadPoolExecutor
    3. Supporting flexible DataFrame input with validation

    Example:
        portfolio = Portfolio('IRSwap', '2024-12-31')
        portfolio.load_trades_from_dataframe(df_trades)
        results = portfolio.price(max_workers=4)
    """

    def __init__(self, trade_type: str, evaluation_date: str):
        """Initialize Portfolio for a specific trade type.

        Args:
            trade_type: The type of trades to price (e.g., 'IRSwap', 'OISwap')
            evaluation_date: The valuation date for all trades
        """
        self.trade_type = trade_type
        self.evaluation_date = evaluation_date
        self.trades = []
        self.market_data = None
        self.results = {}

        # Import the trade class dynamically
        self._trade_class = self._get_trade_class(trade_type)

    def _get_trade_class(self, trade_type: str):
        """Dynamically import the trade class based on trade type.

        Args:
            trade_type: The trade type name

        Returns:
            The trade class

        Raises:
            ImportError: If the trade class cannot be imported
        """
        try:
            # Map trade types to their modules
            trade_module_map = {
                'IRSwap': 'project.qld.trade.ir.irswap',
                'OISwap': 'project.qld.trade.ir.oiswap',
                'IRFixedRateBond': 'project.qld.trade.ir.ir_fixed_rate_bond',
                'CallableCCS': 'project.qld.trade.ir.callable_ccs'
            }

            if trade_type not in trade_module_map:
                raise ValueError(f"Unsupported trade type: {trade_type}")

            module_name = trade_module_map[trade_type]
            module = importlib.import_module(module_name)
            return getattr(module, trade_type)

        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import trade class {trade_type}: {e}")

    def _load_market_data(self, risk_conf: Optional[riskconf.RiskConfiguration] = None):
        """Load market data to be shared across all trades.

        Args:
            risk_conf: Risk configuration for scenario analysis
        """
        if risk_conf is None:
            risk_conf = riskconf.RiskConfiguration(riskconf.RiskType.NPV, None, 1.0)

        market_data_path = MARKET_DATA_PATH / self.trade_type
        if not market_data_path.exists():
            raise FileNotFoundError(f"Market data directory not found: {market_data_path}")

        mktDicRaw = marketTools.loadMarketDataFrameDirectory(market_data_path)
        self.market_data = marketTools.parseMarketDataFrameDictionary(mktDicRaw, risk_conf)
        logger.info(f"Loaded market data for {self.trade_type} from {market_data_path}")

    def load_trades_from_dataframe(self, df: pd.DataFrame, validate: bool = True) -> None:
        """Load trades from a pandas DataFrame.

        Args:
            df: DataFrame containing trade parameters
            validate: Whether to validate DataFrame columns

        Raises:
            ValueError: If DataFrame validation fails
        """
        if validate:
            self._validate_dataframe(df)

        self.trades = []
        for index, row in df.iterrows():
            try:
                # Convert row to dict and add evaluation_date
                trade_params = row.to_dict()
                trade_params['evaluation_date'] = self.evaluation_date

                # Create trade instance
                trade = self._trade_class(**trade_params)

                # Store trade with its index for result mapping
                self.trades.append({'index': index, 'trade': trade, 'params': trade_params})

            except Exception as e:
                logger.error(f"Failed to create trade at index {index}: {e}")
                raise ValueError(f"Failed to create trade at index {index}: {e}")

        logger.info(f"Loaded {len(self.trades)} trades of type {self.trade_type}")

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate that the DataFrame contains required columns for the trade type.

        Args:
            df: DataFrame to validate

        Raises:
            ValueError: If required columns are missing
        """
        if df.empty:
            raise ValueError("DataFrame is empty")

        # Get required parameters from trade class __init__ method
        signature = inspect.signature(self._trade_class.__init__)
        required_params = []

        for param_name, param in signature.parameters.items():
            if param_name not in ['self', 'evaluation_date'] and param.default == inspect.Parameter.empty:
                required_params.append(param_name)

        missing_columns = []
        for param in required_params:
            if param not in df.columns:
                missing_columns.append(param)

        if missing_columns:
            raise ValueError(f"Missing required columns for {self.trade_type}: {missing_columns}")

        logger.info(f"DataFrame validation passed for {self.trade_type}")

    def _price_single_trade(self, trade_info: Dict[str, Any], risk_conf: Optional[riskconf.RiskConfiguration] = None) -> Dict[str, Any]:
        """Price a single trade.

        Args:
            trade_info: Dictionary containing trade instance and metadata
            risk_conf: Risk configuration for scenario analysis

        Returns:
            Dictionary with pricing results
        """
        trade = trade_info['trade']
        index = trade_info['index']

        try:
            # make sure to clear market data or previously calculated results
            trade.reset()

            # Inject shared market data to avoid reloading
            trade.set_market_data(self.market_data)

            # Price the trade
            trade.price(risk_conf)
            trade.calculate_xva()

            result = {
                'trade_id': index,
                'trade_type': self.trade_type,
                'success': True,
                'error': ''
            }
            result.update(trade.result)

            return result

        except Exception as e:
            logger.error(f"Failed to price trade at index {index}: {e}")
            return {
                'trade_id': index,
                'trade_type': self.trade_type,
                'success': False,
                'error': str(e),
                'npv': 0.0,
                'result': {}
            }

    def price(self, risk_conf: Optional[riskconf.RiskConfiguration] = None, max_workers: Optional[int] = None) -> Dict[str, Any]:
        """Price all trades in parallel.

        Args:
            risk_conf: Risk configuration for scenario analysis
            max_workers: Maximum number of worker threads (default: cpu_count)

        Returns:
            Dictionary containing aggregated results

        Raises:
            ValueError: If no trades are loaded
        """
        if not self.trades:
            raise ValueError("No trades loaded. Call load_trades_from_dataframe() first.")

        # Load market data once if not already loaded
        if self.market_data is None:
            self._load_market_data(risk_conf)

        # Determine number of workers
        if max_workers is None:
            max_workers = os.cpu_count()

        logger.info(f"Pricing {len(self.trades)} trades using {max_workers} workers")

        # Price trades in parallel
        trade_results = []
        successful_trades = 0
        failed_trades = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all pricing tasks
            future_to_trade = {
                executor.submit(self._price_single_trade, trade_info, risk_conf): trade_info
                for trade_info in self.trades
            }

            # Collect trade_results as they complete
            for future in as_completed(future_to_trade):
                result = future.result()
                trade_results.append(result)

                if result['success']:
                    successful_trades += 1
                else:
                    failed_trades += 1

        # Calculate portfolio-level NPV
        portfolio_npv = sum(result.get('npv', 0.0) for result in trade_results if result['success'])
        portfolio_cva = sum(result.get('cva', 0.0) for result in trade_results if result['success'])
        portfolio_dva = sum(result.get('dva', 0.0) for result in trade_results if result['success'])

        portfolio_results = {
            'trade_results': trade_results,
            'trade_type': self.trade_type,
            'evaluation_date': self.evaluation_date,
            'trade_count': len(self.trades),
            'successful_trades': successful_trades,
            'failed_trades': failed_trades,
            'portfolio_npv': portfolio_npv,
            'portfolio_cva': portfolio_cva,
            'portfolio_dva': portfolio_dva
        }

        self.results = portfolio_results
        logger.info(f"Portfolio pricing completed: {successful_trades} successful, {failed_trades} failed")
        return portfolio_results

    def calculate_risk_sensitivity(self, curve_name: str, bump_points: Optional[List[float]] = None,
                                   bump_type: Union[str, riskconf.BumpType] = riskconf.BumpType.Absolute,
                                   max_workers: Optional[int] = None) -> Dict[str, Any]:
        """Calculate risk sensitivity for the entire portfolio.

        Args:
            curve_name: Name of the curve to bump
            bump_points: List of bump sizes in basis points
            bump_type: Type of bump (Absolute or Relative)
            max_workers: Maximum number of worker threads

        Returns:
            Dictionary containing portfolio risk sensitivity results
        """
        if not self.trades:
            raise ValueError("No trades loaded. Call load_trades_from_dataframe() first.")

        if bump_points is None:
            bump_points = [1, 5, 10, 25, 50]

        # Get base portfolio NPV
        base_results = self.price(max_workers=max_workers)
        base_portfolio_npv = base_results['portfolio_npv']
        base_portfolio_cva = base_results['portfolio_cva']
        base_portfolio_dva = base_results['portfolio_dva']

        portfolio_risk_results = {
            'base_portfolio_npv': base_portfolio_npv,
            'base_portfolio_cva': base_portfolio_cva,
            'base_portfolio_dva': base_portfolio_dva,
            'bump_points': [],
            'portfolio_npv_values': [],
            'portfolio_cva_values': [],
            'portfolio_dva_values': [],
            'portfolio_npv_changes': [],
            'trade_results': []
        }

        logger.info(f"Calculating portfolio risk sensitivity for curve: {curve_name}")

        # Calculate risk for each bump scenario
        for bump_bp in bump_points:
            logger.info(f"Processing bump: {bump_bp} bp")

            bump_size = bump_bp / 10000  # Convert bp to decimal
            bump_details = riskconf.BumpDetails(None)
            bump_object = riskconf.BumpObject(
                bumpObjectName=curve_name,
                position=-1,  # -1 means parallel bump
                bumpSize=bump_size,
                bumpType=bump_type if isinstance(bump_type, riskconf.BumpType) else riskconf.BumpType[bump_type],
                details=bump_details
            )

            bump_risk_conf = riskconf.RiskConfiguration(
                riskconf.RiskType.NPV,
                [bump_object],
                1.0
            )

            # Price portfolio with bumped market data
            self.reset()
            bumped_results = self.price(bump_risk_conf, max_workers=max_workers)
            bumped_portfolio_npv = bumped_results['portfolio_npv']
            bumped_portfolio_cva = bumped_results['portfolio_cva']
            bumped_portfolio_dva = bumped_results['portfolio_dva']
            portfolio_npv_change = bumped_portfolio_npv - base_portfolio_npv

            portfolio_risk_results['bump_points'].append(bump_bp)
            portfolio_risk_results['portfolio_npv_values'].append(bumped_portfolio_npv)
            portfolio_risk_results['portfolio_cva_values'].append(bumped_portfolio_cva)
            portfolio_risk_results['portfolio_dva_values'].append(bumped_portfolio_dva)
            portfolio_risk_results['portfolio_npv_changes'].append(portfolio_npv_change)
            portfolio_risk_results['trade_results'].append(bumped_results['trade_results'])

        logger.info("Portfolio risk sensitivity calculation completed")
        return portfolio_risk_results

    def reset(self):
        self.results = {}
        self.market_data = None
