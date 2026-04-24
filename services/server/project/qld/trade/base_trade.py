from abc import ABC, abstractmethod
from pathlib import Path

from project.qld.engine.utils.market import marketTools
from project.qld.engine.utils.pricing import riskConfiguration as riskconf
from project.logger import get_logger


logger = get_logger(__name__)


MARKET_DATA_PATH = Path("project/data/db")


class BaseTrade(ABC):
    """Abstract base class for all trade types providing common infrastructure."""

    def __init__(self, evaluation_date, **kwargs):
        """Initialize common trade attributes.

        Args:
            evaluation_date: The valuation date for the trade
            **kwargs: Trade-specific parameters passed to subclasses
        """
        self.evaluation_date = evaluation_date
        self.result = {}
        self.market_data = False

    def _load_market_data(self, risk_conf=None):
        """Load and parse market data for this trade type.

        Args:
            risk_conf: Risk configuration for scenario analysis.
                      Defaults to NPV calculation if None.
        """
        if risk_conf is None:
            risk_conf = riskconf.RiskConfiguration(riskconf.RiskType.NPV, None, 1.0)

        market_data_path = MARKET_DATA_PATH / self.__name__
        market_data_raw = marketTools.loadMarketDataFrameDirectory(market_data_path)
        self.market_data = marketTools.parseMarketDataFrameDictionary(market_data_raw, risk_conf)

    def set_market_data(self, market_data):
        self.market_data = market_data.copy()

    @abstractmethod
    def _parse_input(self):
        """Parse and convert string inputs to QuantLib objects.

        Subclasses must implement this to convert their specific parameters
        (dates, currencies, frequencies, etc.) to appropriate QuantLib types.
        """
        pass

    @abstractmethod
    def _validate_input(self):
        """Validate trade parameters for consistency and business rules.

        Subclasses should implement validation logic specific to their trade type,
        such as ensuring start_date < end_date, positive notionals, etc.
        """
        pass

    @abstractmethod
    def _build_trade(self):
        """Construct the QuantLib trade object.

        Returns:
            The constructed QuantLib instrument object for this trade.
        """
        pass

    def reset(self):
        self.result = {}
        self.market_data = None

    def setup(self, risk_conf=None):
        """Orchestrate the setup process for trade pricing.

        This method coordinates the three setup phases:
        1. Load market data (if not exist)
        2. Parse input parameters
        3. Validate parameters

        Args:
            risk_conf: Risk configuration for scenario analysis
        """
        if not self.market_data:
            self._load_market_data(risk_conf)

    @abstractmethod
    def price(self, risk_conf=None):
        """Price the trade and populate the result dictionary.

        Subclasses must implement the full pricing logic including:
        1. Calling setup()
        2. Building the trade object
        3. Setting the pricing engine
        4. Computing NPV and storing in self.result

        Args:
            risk_conf: Risk configuration for scenario analysis
        """
        pass

    def calculate_xva(self):
        if self.result is None:
            raise Exception('Trade must be priced before calculating XVA')

        if 'npv' not in self.result:
            raise Exception('Trade must be priced before calculating XVA')

        base_npv = self.result['npv']
        self.result['cva'] = base_npv * (1.137/100)
        self.result['dva'] = base_npv * (-1.942/100)

    def calculate_risk_sensitivity(self, curve_name=None, bump_points=None, bump_type=riskconf.BumpType.Absolute):
        """Calculate risk sensitivity across multiple bump scenarios.

        Args:
            curve_name: Name of the curve to bump. If None, tries to infer from trade
            bump_points: List of bump sizes in basis points. Defaults to [1, 5, 10, 25, 50]
            bump_type: Type of bump (Absolute or Relative)

        Returns:
            dict: Risk sensitivity results with NPV changes and DV01 calculations
        """
        if bump_points is None:
            bump_points = [1, 5, 10, 25, 50]

        if isinstance(bump_points, str):
            bump_points = [float(i) for i in bump_points.split(',')]

        if isinstance(bump_type, str):
            if bump_type == 'Absolute':
                bump_type = riskconf.BumpType.Absolute
            elif bump_type == 'Relative':
                bump_type = riskconf.BumpType.Relative
            else:
                raise ValueError("Invalid bump_type, must be either 'Absolute' or 'Relative', found {bump_type}")

        # Get base NPV
        self.price()
        self.calculate_xva()
        base_npv = self.result['npv']
        base_cva = self.result['cva']
        base_dva = self.result['dva']
        base_exposures = self.result.get('exposures', None)

        risk_results = {
            'base_npv': base_npv,
            'base_cva': base_cva,
            'base_dva': base_dva,
            'bump_points': [],
            'npv_values': [],
            'cva_values': [],
            'dva_values': [],
            'exposures': base_exposures,
            'npv_changes': [],
            'dv01_estimates': []
        }

        # If no curve specified, only run base npv
        if curve_name is None or curve_name == '':
            # raise ValueError("curve_name must be specified or trade must have discounting_curve attribute")
            return risk_results

        # Calculate NPV for each bump scenario
        for bump_bp in bump_points:
            bump_size = bump_bp / 10000  # Convert bp to decimal
            bump_details = riskconf.BumpDetails(None)
            bump_object = riskconf.BumpObject(
                bumpObjectName=curve_name,
                position=-1,  # -1 means parallel bump (all tenors)
                bumpSize=bump_size,
                bumpType=bump_type,
                details=bump_details
            )

            bump_risk_conf = riskconf.RiskConfiguration(
                riskconf.RiskType.NPV,
                [bump_object],
                1.0
            )

            # Price with bumped market data
            self.reset()
            self.price(bump_risk_conf)
            self.calculate_xva()
            bumped_npv = self.result['npv']
            bumped_cva = self.result['cva']
            bumped_dva = self.result['dva']
            bumped_exposures = self.result.get('exposures', None)

            if base_exposures is not None and bumped_exposures is not None:
                bumped_exposures.columns = [f'{c}@{bump_bp}bp' if c != 'Date' else c for c in bumped_exposures.columns]
                base_exposures = base_exposures.merge(bumped_exposures, on='Date', how='left')

            npv_change = bumped_npv - base_npv
            dv01_estimate = npv_change / bump_bp  # DV01 per basis point

            risk_results['bump_points'].append(bump_bp)
            risk_results['npv_values'].append(bumped_npv)
            risk_results['cva_values'].append(bumped_cva)
            risk_results['dva_values'].append(bumped_dva)
            risk_results['exposures'] = base_exposures
            risk_results['npv_changes'].append(npv_change)
            risk_results['dv01_estimates'].append(dv01_estimate)
            logger.info(f"Result for bump {bump_bp}: {risk_results}")

        return risk_results
