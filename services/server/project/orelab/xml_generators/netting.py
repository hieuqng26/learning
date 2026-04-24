"""
Netting XML generator.
"""

from lxml import etree
from pathlib import Path
from typing import Optional
import pandas as pd

from ..config import DEFAULTS
from ..trade_builders.base import ValidationResult
from ..utils import validate_currency
from project.logger import get_logger

logger = get_logger(__name__)


class NettingGenerator:
    """
    Generate netting.xml from netting set data.

    Creates CSA (Credit Support Annex) configuration for counterparties.
    """

    REQUIRED_COLUMNS = ["NettingSetId", "CounterParty"]

    def __init__(self, skip_invalid: bool = True, warn_on_skip: bool = True):
        """Initialize netting generator."""
        self.skip_invalid = skip_invalid
        self.warn_on_skip = warn_on_skip
        self.skipped_sets = []

    def validate(self, netting_data: dict) -> ValidationResult:
        """Validate netting set data."""
        result = ValidationResult()

        # Check required fields
        for col in self.REQUIRED_COLUMNS:
            value = netting_data.get(col)
            if value is None or value == "" or str(value).strip() == "":
                result.add_error(f"Missing required field: {col}")

        if not result.is_valid:
            return result

        # Validate CSA threshold and MTA
        try:
            threshold = float(netting_data.get("CSAThreshold", 0))
            if threshold < 0:
                result.add_warning(f"CSA threshold is negative: {threshold}")
        except (ValueError, TypeError):
            result.add_warning(f"Invalid CSA threshold: {netting_data.get('CSAThreshold')}")

        try:
            mta = float(netting_data.get("CSAMta", 0))
            if mta < 0:
                result.add_warning(f"CSA MTA is negative: {mta}")
        except (ValueError, TypeError):
            result.add_warning(f"Invalid CSA MTA: {netting_data.get('CSAMta')}")

        # Validate collateral currency if present
        coll_ccy = netting_data.get("CollateralCurrency")
        if coll_ccy and not validate_currency(coll_ccy):
            result.add_error(f"Invalid collateral currency: {coll_ccy}")

        return result

    def generate(self, netting_df: pd.DataFrame) -> etree.Element:
        """
        Generate netting XML from DataFrame.

        Args:
            netting_df: DataFrame with netting set data

        Returns:
            NettingSetDefinitions XML element
        """
        # Create root element
        netting_sets = etree.Element("NettingSetDefinitions")

        for idx, row in netting_df.iterrows():
            netting_data = row.to_dict()

            # Validate netting set
            validation_result = self.validate(netting_data)

            if not validation_result.is_valid:
                netting_id = netting_data.get("NettingSetId", f"Row_{idx}")
                if self.skip_invalid:
                    self.skipped_sets.append({
                        "netting_id": netting_id,
                        "errors": validation_result.errors
                    })
                    if self.warn_on_skip:
                        logger.warning(f"Skipping invalid netting set {netting_id}:")
                        for error in validation_result.errors:
                            logger.warning(f"   - {error}")
                    continue
                else:
                    error_msg = f"Invalid netting set {netting_id}: " + "; ".join(validation_result.errors)
                    raise ValueError(error_msg)

            # Show warnings
            if validation_result.warnings and self.warn_on_skip:
                netting_id = netting_data.get("NettingSetId", f"Row_{idx}")
                logger.warning(f"Warnings for netting set {netting_id}:")
                for warning in validation_result.warnings:
                    logger.warning(f"   - {warning}")

            netting_set = self._create_netting_set(netting_data)
            netting_sets.append(netting_set)

        return netting_sets

    def _create_netting_set(self, netting_data: dict) -> etree.Element:
        """
        Create a single netting set definition.

        Args:
            netting_data: Dictionary with netting set parameters

        Returns:
            NettingSet XML element (ORE format)
        """
        # Get netting set ID
        netting_id = netting_data.get("NettingSetId", "")
        if not netting_id:
            raise ValueError("NettingSetId is required")

        # Create NettingSet element (not NettingSetDefinition)
        netting_set = etree.Element("NettingSet")

        # NettingSetId as child element
        etree.SubElement(netting_set, "NettingSetId").text = netting_id

        # ActiveCSAFlag
        active_csa = netting_data.get("ActiveCSA", False)
        etree.SubElement(netting_set, "ActiveCSAFlag").text = str(active_csa).lower()

        # CSADetails
        csa_details = etree.SubElement(netting_set, "CSADetails")

        # Bilateral
        etree.SubElement(csa_details, "Bilateral").text = "Bilateral"

        # CSA Currency
        coll_ccy = netting_data.get("CollateralCurrency", DEFAULTS["CollateralCurrency"])
        etree.SubElement(csa_details, "CSACurrency").text = coll_ccy

        # Index (for collateral compounding)
        index = netting_data.get("Index", "EUR-EONIA")
        etree.SubElement(csa_details, "Index").text = index

        # Thresholds (Pay and Receive)
        threshold = netting_data.get("CSAThreshold", DEFAULTS["CSAThreshold"])
        etree.SubElement(csa_details, "ThresholdPay").text = str(threshold)
        etree.SubElement(csa_details, "ThresholdReceive").text = str(threshold)

        # Minimum Transfer Amount (Pay and Receive)
        mta = netting_data.get("CSAMta", DEFAULTS["CSAMta"])
        etree.SubElement(csa_details, "MinimumTransferAmountPay").text = str(mta)
        etree.SubElement(csa_details, "MinimumTransferAmountReceive").text = str(mta)

        # Independent Amount
        independent_amt = etree.SubElement(csa_details, "IndependentAmount")
        ia_held = netting_data.get("IndependentAmountHeld", 0)
        etree.SubElement(independent_amt, "IndependentAmountHeld").text = str(ia_held)
        etree.SubElement(independent_amt, "IndependentAmountType").text = "FIXED"

        # Margining Frequency
        margining_freq = etree.SubElement(csa_details, "MarginingFrequency")
        margin_call_freq = netting_data.get("MarginCallFrequency", DEFAULTS["MarginCallFrequency"])
        margin_post_freq = netting_data.get("MarginPostFrequency", DEFAULTS["MarginPostFrequency"])
        etree.SubElement(margining_freq, "CallFrequency").text = margin_call_freq
        etree.SubElement(margining_freq, "PostFrequency").text = margin_post_freq

        # Margin Period of Risk (in weeks format like "2W" or "0W")
        mpr = netting_data.get("MarginPeriodOfRisk", "0W")
        if isinstance(mpr, int):
            mpr = f"{mpr // 7}W" if mpr >= 7 else "0W"
        etree.SubElement(csa_details, "MarginPeriodOfRisk").text = str(mpr)

        # Collateral Compounding Spreads
        etree.SubElement(csa_details, "CollateralCompoundingSpreadReceive").text = "0.0"
        etree.SubElement(csa_details, "CollateralCompoundingSpreadPay").text = "0.0"

        # Eligible Collaterals
        eligible = etree.SubElement(csa_details, "EligibleCollaterals")
        currencies = etree.SubElement(eligible, "Currencies")
        etree.SubElement(currencies, "Currency").text = coll_ccy

        return netting_set

    def save_to_file(self, netting_sets: etree.Element, output_path: Path) -> None:
        """
        Save netting XML to file.

        Args:
            netting_sets: NettingSetDefinitions XML element
            output_path: Path to output file
        """
        tree = etree.ElementTree(netting_sets)
        tree.write(
            str(output_path),
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )
