"""
Main Excel-to-ORE conversion engine.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import warnings
import pandas as pd
from datetime import datetime
import ORE

from .excel_reader import ExcelTradeReader
from .xml_generators import (
    PortfolioGenerator,
    NettingGenerator,
    OREConfigGenerator,
    SensitivityGenerator,
    ScenarioGenerator,
    SimulationGenerator,
    XVASensiMarketGenerator
)
from .config import INPUT_PATH, STATIC_PATH, OUTPUT_PATH, DATE_FORMAT_DISPLAY
from .utils import create_temp_folder, cleanup_temp_folder, format_date_for_ore
from project.logger import get_logger

logger = get_logger(__name__)


class OREBuilder:
    """
    Excel to ORE converter with context manager interface.

    Usage:
        with OREBuilder('trades.xlsx', cleanup=True) as converter:
            ore_config_path = converter.ore_config_path
            # Run ORE with the generated configuration
            # Temp folder will be cleaned up automatically on exit

        # Override asofDate in ore.xml
        with OREBuilder('trades.xlsx', asof_date='2024-03-15') as converter:
            ore_config_path = converter.ore_config_path

    The converter:
    1. Reads Excel file with trade data
    2. Validates trades
    3. Generates portfolio.xml and netting.xml
    4. Creates ore.xml with updated paths
    5. Optionally overrides asofDate parameter
    6. Returns path to temporary folder with all configs
    """

    def __init__(
        self,
        input: str | dict,
        asof_date: str,
        base_currency: str = "EUR",
        template_ore_xml: Optional[str] = None,
        cleanup: bool = True,
        skip_invalid: bool = True,
        warn_on_skip: bool = True,
        sensitivity_config: Optional[Dict[str, Any]] = None,
        scenario_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize OREBuilder.

        Args:
            input: Path to Excel file with trade data or a dictionary of trade data
            asof_date: As-of date to override in ore.xml (YYYY-MM-DD or YYYYMMDD format)
            template_ore_xml: Path to template ore.xml (default: Input/ore.xml)
            cleanup: Whether to cleanup temp folder on exit
            skip_invalid: Whether to skip invalid trades
            warn_on_skip: Whether to print warnings for skipped trades
            sensitivity_config: Optional dict with sensitivity analysis configuration
            scenario_config: Optional dict with scenario/stress test configuration

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If asof_date format is invalid
        """
        self.input = input

        # Set template path
        if template_ore_xml:
            self.template_ore_xml = Path(template_ore_xml)
        else:
            self.template_ore_xml = INPUT_PATH / "ore.xml"

        # Validate and store asof_date
        if asof_date:
            # Validate and convert to YYYY-MM-DD format for ore.xml
            try:
                # format_date_for_ore returns YYYYMMDD, we need to convert to YYYY-MM-DD
                validated_date = format_date_for_ore(asof_date)
                dt = datetime.strptime(validated_date, "%Y%m%d")
                self.asof_date = dt.strftime(DATE_FORMAT_DISPLAY)
            except ValueError as e:
                raise ValueError(f"Invalid asof_date format: {asof_date}. {str(e)}")
        else:
            self.asof_date = None

        self.base_currency = base_currency
        self.cleanup = cleanup
        self.skip_invalid = skip_invalid
        self.warn_on_skip = warn_on_skip
        self.sensitivity_config = sensitivity_config
        self.scenario_config = scenario_config

        # Will be set during conversion
        self.temp_folder: Optional[Path] = None
        self.ore_config_path: Optional[Path] = None
        self.portfolio_path: Optional[Path] = None
        self.netting_path: Optional[Path] = None
        self.sensitivity_path: Optional[Path] = None
        self.scenario_path: Optional[Path] = None

        # Components
        self.reader: Optional[ExcelTradeReader] = None
        self.portfolio_generator: Optional[PortfolioGenerator] = None
        self.netting_generator: Optional[NettingGenerator] = None
        self.sensitivity_generator: Optional[SensitivityGenerator] = None
        self.scenario_generator: Optional[ScenarioGenerator] = None

    def __enter__(self):
        """
        Enter context manager - perform conversion.

        Returns:
            Self with temp_folder and ore_config_path set
        """
        self.convert()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - cleanup if requested.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.cleanup and self.temp_folder:
            cleanup_temp_folder(self.temp_folder)
            logger.info(f"Cleaned up temporary folder: {self.temp_folder}")

    def convert(self) -> Path:
        """
        Perform full conversion from Excel to ORE XML files.

        Returns:
            Path to generated ore.xml configuration file

        Raises:
            ValueError: If conversion fails
        """
        logger.info("=" * 60)
        logger.info("Starting ORE Builder")
        logger.info("=" * 60)

        inputs = self._get_inputs()
        self._create_temp_folder()
        self._generate_portfolio(inputs)
        self._generate_netting(inputs)
        self._generate_sensitivity()
        self._generate_scenario()
        self._generate_simulation()
        self._generate_xvasensimarket()
        self._generate_ore_config()

        return self.ore_config_path

    def _create_temp_folder(self) -> None:
        """Create temporary folder for generated files."""
        logger.info("Creating temporary folder...")
        self.temp_folder = create_temp_folder(INPUT_PATH)
        logger.info(f"Created: {self.temp_folder}")

    def _generate_portfolio(self, inputs: dict) -> None:
        """Generate portfolio.xml from trade inputs."""
        logger.info("Generating portfolio.xml...")
        self.portfolio_generator = PortfolioGenerator(
            skip_invalid=self.skip_invalid,
            warn_on_skip=self.warn_on_skip
        )
        portfolio_elem = self.portfolio_generator.generate(
            trades=inputs.get('trades', {})
        )
        self.portfolio_path = self.temp_folder / "portfolio.xml"
        self.portfolio_generator.save_to_file(portfolio_elem, self.portfolio_path)
        logger.info(f"Saved: {self.portfolio_path}")

    def _generate_netting(self, inputs: dict) -> None:
        """Generate netting.xml if netting data exists."""
        netting_df = inputs.get('netting_sets')
        if netting_df is not None and not netting_df.empty:
            logger.info("Generating netting.xml...")
            self.netting_generator = NettingGenerator()
            netting_elem = self.netting_generator.generate(netting_df)
            self.netting_path = self.temp_folder / "netting.xml"
            self.netting_generator.save_to_file(netting_elem, self.netting_path)
            logger.info(f"Saved: {self.netting_path}")

    def _generate_sensitivity(self) -> None:
        """Generate sensitivity.xml if sensitivity config exists."""
        if self.sensitivity_config is not None:
            logger.info("Sensitivity analysis: ENABLED")
            logger.info(f"Risk factors: {', '.join(self.sensitivity_config.keys())}")
            logger.info("Generating sensitivity.xml...")
            self.sensitivity_generator = SensitivityGenerator()
            sensitivity_elem = self.sensitivity_generator.generate(self.sensitivity_config)
            self.sensitivity_path = self.temp_folder / "sensitivity.xml"
            self.sensitivity_generator.save_to_file(sensitivity_elem, self.sensitivity_path)
            logger.info(f"Saved: {self.sensitivity_path}")

    def _generate_scenario(self) -> None:
        """Generate scenarios.xml if scenario config exists."""
        if self.scenario_config is not None:
            logger.info("Scenario/Stress testing: ENABLED")
            logger.info(f"Number of scenarios: {len(self.scenario_config.get('scenarios', []))}")
            logger.info("Generating scenarios.xml...")
            self.scenario_generator = ScenarioGenerator()
            scenario_elem = self.scenario_generator.generate(self.scenario_config)
            self.scenario_path = self.temp_folder / "scenarios.xml"
            self.scenario_generator.save_to_file(scenario_elem, self.scenario_path)
            logger.info(f"Saved: {self.scenario_path}")

    def _generate_simulation(self) -> Path:
        """Generate simulation.xml with base currency."""
        logger.info("Generating simulation.xml...")
        simulation_path = self.temp_folder / "simulation.xml"
        simulation_generator = SimulationGenerator(STATIC_PATH / "simulation.xml")
        simulation_generator.load_template()
        simulation_generator.set_base_currency(self.base_currency)
        simulation_generator.save_to_file(simulation_path)
        logger.info(f"Saved: {simulation_path}")
        self.simulation_path = simulation_path

    def _generate_xvasensimarket(self) -> Path:
        """Generate xvasensimarket.xml with base currency."""
        logger.info("Generating xvasensimarket.xml...")
        xvasensimarket_path = self.temp_folder / "xvasensimarket.xml"
        xvasensimarket_generator = XVASensiMarketGenerator(INPUT_PATH / "xvasensimarket.xml")
        xvasensimarket_generator.load_template()
        xvasensimarket_generator.set_base_currency(self.base_currency)
        xvasensimarket_generator.save_to_file(xvasensimarket_path)
        logger.info(f"Saved: {xvasensimarket_path}")
        self.xvasensimarket_path = xvasensimarket_path

    def _generate_ore_config(self) -> None:
        """Generate ore.xml configuration file."""
        logger.info("Generating ore.xml...")
        ore_generator = OREConfigGenerator(self.template_ore_xml)
        ore_generator.load_template()

        self.output_path = os.path.join(OUTPUT_PATH, self.temp_folder.name)

        ore_generator.update_paths(
            input_path=str(INPUT_PATH),
            output_path=str(self.output_path),
            portfolio_file=str(self.portfolio_path) if self.portfolio_path else None,
            netting_file=str(self.netting_path) if self.netting_path else None,
            static_path_prefix=str(STATIC_PATH)+'/',
            simulation_config_file=str(self.simulation_path),
            sensitivity_file=str(self.sensitivity_path) if self.sensitivity_path else None,
            scenario_file=str(self.scenario_path) if self.scenario_path else None,
            xvasensimarket_file=str(self.xvasensimarket_path)
        )

        ore_generator.set_asof_date(self.asof_date)
        ore_generator.set_base_currency(self.base_currency)

        self.ore_config_path = self.temp_folder / "ore.xml"
        ore_generator.save_to_file(self.ore_config_path)
        logger.info(f"Saved: {self.ore_config_path}")

    def _get_inputs(self) -> dict:
        """
        Get dictionary of generated file paths.

        Returns:
            Dictionary with paths to generated files
        """
        if isinstance(self.input, dict):
            if not ('trades' in self.input):
                raise ValueError("Input must contain 'trades'")
            return self.input

        excel_path = Path(self.input)
        if not excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        logger.info("Reading Excel file...")
        self.reader = ExcelTradeReader(str(excel_path))
        self.reader.read_all()

        if self.reader.get_warnings():
            logger.warning("Excel Reader Warnings:")
            for warning in self.reader.get_warnings():
                logger.warning(f"  {warning}")

        return {
            "trades": self.reader.get_all_trades(),
            "netting_sets": self.reader.get_netting_sets()
        }

    def get_generated_files(self) -> dict:
        """
        Get dictionary of generated file paths.

        Returns:
            Dictionary with paths to generated files
        """
        return {
            "temp_folder": self.temp_folder,
            "ore_config": self.ore_config_path,
            "portfolio": self.portfolio_path,
            "netting": self.netting_path
        }

    def get_summary(self) -> dict:
        """
        Get summary of conversion process.

        Returns:
            Dictionary with conversion statistics
        """
        summary = {
            "input": self.input,
            "temp_folder": str(self.temp_folder) if self.temp_folder else None,
            "files_generated": {}
        }

        if self.portfolio_generator:
            summary["portfolio"] = self.portfolio_generator.get_summary()

        if self.reader:
            summary["excel_warnings"] = self.reader.get_warnings()

        return summary


class ORERunner:
    """
    End-to-end ORE execution from Excel to results.

    This class orchestrates the complete workflow:
    1. Convert Excel to XML using OREBuilder
    2. Run OREApp to execute analytics
    3. Parse and store NPV and exposure results
    4. Provide accessor methods for results
    5. Clean up temporary files

    Usage:
        with ORERunner('trades.xlsx') as runner:
            runner.run()

            # Access results
            npv_df = runner.get_npv()
            xva_df = runner.get_xva()

            # Get specific trade data
            trade_npv = runner.get_trade_npv('Trade_123')
            trade_epe = runner.get_trade_exposure('Trade_123')

            # Optionally save results before cleanup
            runner.save_results('/path/to/permanent/location')
        # Auto-cleanup removes temp folders

        # Override asofDate in ore.xml
        with ORERunner('trades.xlsx', asof_date='2024-03-15') as runner:
            runner.run()
    """

    def __init__(
        self,
        input: str | dict,
        cleanup: bool = True,
        **converter_kwargs
    ):
        """
        Initialize ORERunner.

        Args:
            input: Path to Excel file or dictionary with trade data
            cleanup: Whether to cleanup temp folders on exit (default: True)
            **converter_kwargs: Additional arguments passed to OREBuilder
                (e.g., template_ore_xml, asof_date, skip_invalid, warn_on_skip)

        Raises:
            FileNotFoundError: If Excel file doesn't exist
        """
        self.input = input
        self.cleanup = cleanup
        self.converter_kwargs = converter_kwargs

        # Components
        self.converter: Optional[OREBuilder] = None
        self.output_path: Optional[Path] = None

        # Cached results (lazy-loaded)
        self._npv_df: Optional[pd.DataFrame] = None
        self._xva_df: Optional[pd.DataFrame] = None
        self._exposures: Optional[Dict[str, pd.DataFrame]] = {'trade': None, 'nettingset': None}
        self._sensitivity_df: Optional[pd.DataFrame] = None
        self._xva_sensitivity_exposures: Optional[Dict[str, pd.DataFrame]] = {'trade': None, 'nettingset': None}
        self._stress_df: Optional[pd.DataFrame] = None
        self._xva_stress_exposures: Optional[Dict[str, pd.DataFrame]] = {'trade': None, 'nettingset': None}

        # Execution state
        self._executed: bool = False

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - cleanup if requested."""
        if self.cleanup:
            self.cleanup_files()

    def run(self) -> None:
        """
        Execute the complete ORE workflow.

        Steps:
        1. Convert Excel to XML files
        2. Run ORE analytics
        3. Parse result files

        Raises:
            RuntimeError: If ORE execution fails
            ImportError: If ORE module not available
        """
        if self._executed:
            warnings.warn("ORE has already been executed. Skipping re-run.")
            return

        # Step 1: Build XML
        logger.info("=" * 60)
        logger.info("Build XML")
        logger.info("=" * 60)

        self.converter = OREBuilder(
            input=self.input,
            cleanup=False,  # Use OREBuilder but don't auto-cleanup (we'll manage it)
            **self.converter_kwargs
        )

        ore_config_path = self.converter.convert()
        self.output_path = Path(self.converter.output_path)

        # Step 2: Run ORE
        logger.info("=" * 60)
        logger.info("Running ORE Analytics")
        logger.info("=" * 60)

        params = ORE.Parameters()
        params.fromFile(str(ore_config_path))
        app = ORE.OREApp(params, True)  # True = console mode
        app.run()

        logger.info("ORE execution completed")
        logger.info(f"Results written to: {self.output_path}")

        # Step 3: Parse results
        logger.info("=" * 60)
        logger.info("Parsing Results")
        logger.info("=" * 60)
        self._parse_results()

        self._executed = True

    def _parse_results(self) -> None:
        """Parse ORE output files into DataFrames."""
        if not self.output_path or not self.output_path.exists():
            warnings.warn(f"Output path not found: {self.output_path}")
            return

        self._parse_npv()
        self._parse_xva()
        self._parse_exposures()
        self._parse_sensitivity()
        self._parse_xva_sensitivity_exposures()
        self._parse_stress()
        self._parse_xva_stress_exposures()

    def _parse_npv(self) -> None:
        """Parse NPV results."""
        try:
            npv_file = self.output_path / "npv.csv"
            if not npv_file.exists():
                raise FileNotFoundError(f"NPV file not found: {npv_file}")

            self._npv_df = pd.read_csv(npv_file)
            self._npv_df.columns = [c.replace('#', '') for c in self._npv_df.columns]

            logger.info("Parsed NPV results")
        except FileNotFoundError:
            logger.warning("NPV results file not found")

    def _parse_xva(self) -> None:
        """Parse XVA results."""
        try:
            xva_file = self.output_path / "xva.csv"
            if not xva_file.exists():
                xva_file = self.output_path / "XVA_SENSITIVITY_xva_0.csv"
                if not xva_file.exists():
                    raise FileNotFoundError(f"XVA file not found: {xva_file}")
            self._xva_df = pd.read_csv(xva_file)
            self._xva_df.columns = [c.replace('#', '') for c in self._xva_df.columns]

            if 'Type' not in self._xva_df.columns:
                self._xva_df['Type'] = 'Base'

            logger.info("Parsed XVA results")
        except FileNotFoundError:
            logger.warning("XVA results file not found")

    def _parse_exposures(self) -> None:
        """Parse exposure results (trade and netting set)."""
        for exposure_type in ['trade', 'nettingset']:
            try:
                pattern = f"exposure_{exposure_type}_*.csv"
                exposure_files = list(self.output_path.glob(pattern))

                if not exposure_files:
                    pattern = f"XVA_exposure_{exposure_type}_*.csv"
                    exposure_files = list(self.output_path.glob(pattern))
                    if not exposure_files:
                        continue

                # Read and combine all exposure files
                dfs = []
                for file in exposure_files:
                    df = pd.read_csv(file)
                    dfs.append(df)

                combined_df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
                combined_df.columns = [c.replace('#', '') for c in combined_df.columns]

                # Cache result
                self._exposures[exposure_type] = combined_df

                logger.info(f"Parsed {exposure_type} exposure results")
            except Exception as e:
                logger.error(f"Failed to parse {exposure_type} exposure files: {e}")

    def _parse_sensitivity(self) -> None:
        """Parse sensitivity results."""
        try:
            sensitivity_file = self.output_path / "sensitivity.csv"
            if not sensitivity_file.exists():
                # Sensitivity is optional, so don't raise error
                return

            self._sensitivity_df = pd.read_csv(sensitivity_file)
            self._sensitivity_df.columns = [c.replace('#', '') for c in self._sensitivity_df.columns]
            logger.info("Parsed sensitivity results")
        except Exception as e:
            logger.error(f"Failed to parse sensitivity file: {e}")

    def _parse_xva_sensitivity_exposures(self) -> None:
        """Parse exposure results (trade and netting set)."""
        for exposure_type in ['trade', 'nettingset']:
            try:
                pattern = f"XVA_SENSITIVITY_exposure_{exposure_type}_*.csv"
                exposure_files = list(self.output_path.glob(pattern))

                if not exposure_files:
                    continue

                # Read and combine all exposure files
                dfs = []
                for file in exposure_files:
                    df = pd.read_csv(file)
                    dfs.append(df)

                combined_df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
                combined_df.columns = [c.replace('#', '') for c in combined_df.columns]

                # Cache result
                self._xva_sensitivity_exposures[exposure_type] = combined_df

                logger.info(f"Parsed XVA_SENSITIVITY {exposure_type} exposure results")
            except Exception as e:
                logger.error(f"Failed to parse XVA_SENSITIVITY {exposure_type} exposure files: {e}")

    def _parse_stress(self) -> None:
        """Parse stress test results."""
        try:
            stress_file = self.output_path / "stresstest.csv"
            if not stress_file.exists():
                # Stress testing is optional, so don't raise error
                return

            self._stress_df = pd.read_csv(stress_file)
            self._stress_df.columns = [c.replace('#', '') for c in self._stress_df.columns]
            self._stress_df.rename(columns={'ScenarioLabel': 'Scenario'}, inplace=True)
            logger.info("Parsed stress test results")
        except Exception as e:
            logger.error(f"Failed to parse stress test file: {e}")

    def _parse_xva_stress_exposures(self) -> None:
        """Parse stress test results."""
        for exposure_type in ['trade', 'nettingset']:
            try:
                pattern = f"XVA_STRESS_exposure_{exposure_type}_*.csv"
                exposure_files = list(self.output_path.glob(pattern))

                if not exposure_files:
                    continue

                # Read and combine all exposure files
                dfs = []
                for file in exposure_files:
                    df = pd.read_csv(file)
                    dfs.append(df)

                combined_df = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
                combined_df.columns = [c.replace('#', '') for c in combined_df.columns]

                # Cache result
                self._xva_stress_exposures[exposure_type] = combined_df

                logger.info(f"Parsed XVA_STRESS {exposure_type} exposure results")
            except Exception as e:
                logger.error(f"Failed to parse XVA_STRESS {exposure_type} exposure files: {e}")

    def get_npv(self) -> pd.DataFrame:
        """
        Get NPV results as DataFrame.
        """
        return self._npv_df

    def get_xva(self) -> pd.DataFrame:
        """
        Get XVA results as DataFrame.
        """
        return self._xva_df

    def get_exposures(self, exposure_type: str = 'both') -> pd.DataFrame:
        """
        Get exposure profiles (EPE/ENE) as DataFrame.
        """
        if exposure_type == 'both':
            return self._exposures
        elif exposure_type == 'trade' or exposure_type == 'nettingset':
            return self._exposures[exposure_type]
        else:
            raise ValueError(f"Invalid exposure_type: {exposure_type}. Use 'trade' or 'nettingset'")

    def get_sensitivity(self) -> Optional[pd.DataFrame]:
        """
        Get sensitivity results as DataFrame.

        Returns:
            DataFrame with sensitivity results (Delta, Gamma per risk factor)
            or None if sensitivity analysis was not run
        """
        return self._sensitivity_df

    def get_xva_sensitivity_exposures(self, exposure_type: str = 'both') -> Optional[pd.DataFrame]:
        """
        Get XVA sensitivity exposure results as DataFrame.

        Returns:
            DataFrame with XVA sensitivity exposure results (EPE, ENE per risk factor)
            or None if XVA sensitivity analysis was not run
        """
        if exposure_type == 'both':
            return self._xva_sensitivity_exposures
        elif exposure_type == 'trade' or exposure_type == 'nettingset':
            return self._xva_sensitivity_exposures[exposure_type]
        else:
            raise ValueError(f"Invalid exposure_type: {exposure_type}. Use 'trade' or 'nettingset'")

    def get_stress(self) -> Optional[pd.DataFrame]:
        """
        Get stress test results as DataFrame.

        Returns:
            DataFrame with stress test results (Base NPV, Stressed NPV, P&L per scenario)
            or None if stress testing was not run
        """
        return self._stress_df

    def get_xva_stress_exposures(self, exposure_type: str = 'both') -> Optional[pd.DataFrame]:
        """
        Get XVA stress test results as DataFrame.

        Returns:
            DataFrame with XVA stress test results (Base XVA, Stressed XVA, P&L per scenario)
            or None if XVA stress testing was not run
        """
        if exposure_type == 'both':
            return self._xva_stress_exposures
        elif exposure_type == 'trade' or exposure_type == 'nettingset':
            return self._xva_stress_exposures[exposure_type]
        else:
            raise ValueError(f"Invalid exposure_type: {exposure_type}. Use 'trade' or 'nettingset'")

    def save_results(self, destination: str) -> None:
        """
        Copy results to a permanent location before cleanup.

        Args:
            destination: Destination directory path

        Raises:
            ValueError: If results haven't been generated yet
        """
        if not self._executed:
            raise ValueError("Cannot save results - ORE hasn't been executed yet. Call run() first.")

        if not self.output_path or not self.output_path.exists():
            raise ValueError(f"Output path not found: {self.output_path}")

        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Copying results to: {dest_path}")

        # Copy all files from output folder
        for file in self.output_path.glob("*"):
            if file.is_file():
                shutil.copy2(file, dest_path / file.name)

        logger.info(f"Results saved to: {dest_path}")

    def cleanup_files(self) -> None:
        """
        Remove temporary input and output folders.
        """
        removed = []

        # Clean up converter's temp folder (input)
        if self.converter and self.converter.temp_folder:
            if self.converter.temp_folder.exists():
                cleanup_temp_folder(self.converter.temp_folder)
                removed.append(f"Input: {self.converter.temp_folder}")

        # Clean up output folder
        if self.output_path and self.output_path.exists():
            cleanup_temp_folder(self.output_path)
            removed.append(f"Output: {self.output_path}")

        if removed:
            logger.info("Cleaned up temporary folders:")
            for path in removed:
                logger.info(f"  - {path}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution and results.

        Returns:
            Dictionary with execution statistics and result counts
        """
        summary = {
            "input": self.input,
            "executed": self._executed,
            "output_path": str(self.output_path) if self.output_path else None,
        }

        # Add converter summary if available
        if self.converter:
            summary["converter"] = self.converter.get_summary()

        return summary
