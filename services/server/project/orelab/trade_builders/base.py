"""
Base trade builder class.
"""

from abc import ABC, abstractmethod
from lxml import etree
from typing import Dict, Any
from datetime import datetime
import math

from ..config import DATE_FORMAT, DATE_FORMAT_DISPLAY
from ..utils import validate_currency


class ValidationResult:
    """Result of validation check."""

    def __init__(self, is_valid: bool = True, errors: list = None, warnings: list = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        """Add error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """Add warning message."""
        self.warnings.append(warning)

    def __bool__(self):
        """Return validation status."""
        return self.is_valid


class BaseTradeBuilder(ABC):
    """
    Abstract base class for trade builders.

    Each trade builder converts a dictionary of trade data
    into an XML element representing the trade in ORE format.
    """

    def __init__(self, trade_data: Dict[str, Any]):
        """
        Initialize trade builder.

        Args:
            trade_data: Dictionary containing trade parameters
        """
        self.trade_data = trade_data

    @abstractmethod
    def build(self) -> etree.Element:
        """
        Build trade XML element.

        Returns:
            XML Element representing the trade

        Raises:
            ValueError: If trade data is invalid
        """
        pass

    @abstractmethod
    def validate(self) -> ValidationResult:
        """
        Validate trade data.

        Returns:
            ValidationResult with errors and warnings
        """
        pass

    # Subclasses should define this
    REQUIRED_COLUMNS = []

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """
        Check if a value is empty (None, NaN, or empty string).

        Args:
            value: Value to check

        Returns:
            True if value is None, NaN, or empty string
        """
        if value is None:
            return True
        # Check for NaN (works for float NaN)
        try:
            if isinstance(value, float) and math.isnan(value):
                return True
        except (TypeError, ValueError):
            pass
        # Check for empty string
        if str(value).strip() == "":
            return True
        return False

    def _validate_required_fields(self, result: ValidationResult) -> None:
        """Check that all required fields are present."""
        for col in self.REQUIRED_COLUMNS:
            value = self.trade_data.get(col)
            if self._is_empty(value):
                result.add_error(f"Missing required field: {col}")

    def _validate_currency(self, code: Any, field_name: str, result: ValidationResult) -> None:
        """Validate currency code."""
        if not validate_currency(str(code)):
            result.add_error(f"Invalid {field_name}: {code}")

    def _validate_numeric(self, value: Any, field_name: str, result: ValidationResult, positive_only: bool = True) -> None:
        """Validate numeric field."""
        try:
            num = float(value)
            if positive_only and num <= 0:
                result.add_error(f"{field_name} must be positive: {value}")
        except (ValueError, TypeError):
            result.add_error(f"Invalid {field_name}: {value}")

    def _validate_date(self, date_value: Any, field_name: str, result: ValidationResult) -> None:
        """Validate date format - supports both single dates and lists of dates."""
        if not date_value:
            return

        if isinstance(date_value, list):
            for i, date in enumerate(date_value):
                self._validate_single_date(date, f"{field_name}[{i}]", result)
        else:
            self._validate_single_date(date_value, field_name, result)

    def _validate_single_date(self, date_value: Any, field_name: str, result: ValidationResult) -> None:
        """Validate a single date format."""
        if not date_value:
            return

        date_str = str(date_value).strip()
        valid = False
        for fmt in [DATE_FORMAT, DATE_FORMAT_DISPLAY, "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                datetime.strptime(date_str, fmt)
                valid = True
                break
            except ValueError:
                continue

        if not valid:
            result.add_error(f"Invalid date format for {field_name}: {date_value} (expected YYYYMMDD or YYYY-MM-DD)")

    def _validate_tenor(self, tenor: Any, field_name: str, result: ValidationResult) -> None:
        """Validate tenor format (e.g., 1Y, 6M, 3M)."""
        if not tenor:
            return

        tenor_str = str(tenor).strip().upper()
        if not tenor_str or tenor_str[-1] not in ["D", "W", "M", "Y"]:
            result.add_error(f"Invalid tenor format for {field_name}: {tenor} (expected format like 1Y, 6M, 3M)")
            return

        try:
            int(tenor_str[:-1])
        except ValueError:
            result.add_error(f"Invalid tenor format for {field_name}: {tenor} (expected format like 1Y, 6M, 3M)")

    def _create_envelope(self, parent: etree.Element) -> etree.Element:
        """
        Create Envelope element common to all trades.

        Args:
            parent: Parent XML element

        Returns:
            Created Envelope element
        """
        envelope = etree.SubElement(parent, "Envelope")

        # CounterParty
        counterparty = self.trade_data.get("CounterParty", "")
        etree.SubElement(envelope, "CounterParty").text = counterparty

        # NettingSetId - use CounterParty as default
        netting_set = self.trade_data.get("NettingSetId", counterparty)
        etree.SubElement(envelope, "NettingSetId").text = netting_set

        return envelope

    def _get_required(self, key: str, field_name: str = None) -> Any:
        """
        Get required field from trade data.

        Args:
            key: Dictionary key
            field_name: Human-readable field name for error messages

        Returns:
            Field value

        Raises:
            ValueError: If field is missing or empty
        """
        value = self.trade_data.get(key)
        if value is None or value == "" or str(value).strip() == "":
            field_name = field_name or key
            trade_id = self.trade_data.get("TradeId", "Unknown")
            raise ValueError(f"Trade {trade_id}: Missing required field '{field_name}'")
        return value

    def _get_optional(self, key: str, default: Any = None) -> Any:
        """
        Get optional field from trade data with default.

        Args:
            key: Dictionary key
            default: Default value if field is missing

        Returns:
            Field value or default
        """
        value = self.trade_data.get(key, default)
        if value is None or value == "" or str(value).strip() == "":
            return default
        return value

    def _create_text_element(
        self,
        parent: etree.Element,
        tag: str,
        text: Any
    ) -> etree.Element:
        """
        Create XML element with text content.

        Args:
            parent: Parent XML element
            tag: Element tag name
            text: Text content

        Returns:
            Created element
        """
        elem = etree.SubElement(parent, tag)
        elem.text = str(text)
        return elem

    def to_xml_string(self, pretty_print: bool = True) -> str:
        """
        Build trade and return as XML string.

        Args:
            pretty_print: Whether to format XML with indentation

        Returns:
            XML string
        """
        trade_elem = self.build()
        return etree.tostring(
            trade_elem,
            encoding='unicode',
            pretty_print=pretty_print
        )
