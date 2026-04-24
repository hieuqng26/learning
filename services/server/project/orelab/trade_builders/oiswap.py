"""
Overnight Index Swap trade builder.
"""

from lxml import etree
from .base import BaseTradeBuilder, ValidationResult
from ..utils import format_date_for_ore
from ..config import DEFAULTS


class OvernightIndexSwapBuilder(BaseTradeBuilder):
    """
    Build Overnight Index Swap (OIS) trade XML.

    OIS has only a floating leg tied to an overnight rate index.

    Optional fields:
    - FloatingSpread (default: 0.0)
    - Calendar (default: TARGET)
    - Convention (default: MF)
    - PaymentConvention (default: MF)
    - IsInArrears (default: false)
    - FixingDays (default: 2)
    """

    REQUIRED_COLUMNS = [
        "TradeId", "CounterParty", "Currency", "Notional",
        "Payer", "StartDate", "EndDate", "Tenor",
        "FloatingIndex", "DayCounter"
    ]

    def validate(self) -> ValidationResult:
        """Validate Overnight Index Swap trade data."""
        result = ValidationResult()

        # Check required fields first
        self._validate_required_fields(result)
        if not result.is_valid:
            return result

        # Validate currency
        currency = self.trade_data.get("Currency", "")
        self._validate_currency(currency, "Currency", result)

        # Validate notional is positive
        self._validate_numeric(self.trade_data.get("Notional", 0), "Notional", result)

        # Validate dates
        self._validate_date(self.trade_data.get("StartDate"), "StartDate", result)
        self._validate_date(self.trade_data.get("EndDate"), "EndDate", result)

        # Validate tenor
        self._validate_tenor(self.trade_data.get("Tenor"), "Tenor", result)

        # Validate Payer boolean
        payer = str(self.trade_data.get("Payer", "")).lower()
        if payer not in ["true", "false", "1", "0", "yes", "no"]:
            result.add_error(f"Invalid Payer: {self.trade_data.get('Payer')} (expected True or False)")

        return result

    def build(self) -> etree.Element:
        """
        Build Overnight Index Swap trade XML element.

        Returns:
            XML Element for OIS trade
        """
        # Create root Trade element
        trade = etree.Element("Trade", id=self._get_required("TradeId"))

        # TradeType - OIS is represented as Swap in ORE
        etree.SubElement(trade, "TradeType").text = "Swap"

        # Envelope
        self._create_envelope(trade)

        # SwapData
        swap_data = etree.SubElement(trade, "SwapData")

        # Get common parameters
        currency = self._get_required("Currency")
        notional = self._get_required("Notional")
        start_date = format_date_for_ore(self._get_required("StartDate"))
        end_date = format_date_for_ore(self._get_required("EndDate"))
        calendar = self._get_optional("Calendar", DEFAULTS["Calendar"])

        # Get payer flag - for OIS this determines direction
        payer_str = self._get_required("Payer")
        if isinstance(payer_str, str):
            payer = payer_str.lower() in ("true", "yes", "1")
        else:
            payer = bool(payer_str)

        # Create Floating Leg (only leg for OIS)
        self._create_floating_leg(
            swap_data,
            payer=payer,
            currency=currency,
            notional=notional,
            start_date=start_date,
            end_date=end_date,
            calendar=calendar
        )

        return trade

    def _create_floating_leg(
        self,
        swap_data: etree.Element,
        payer: bool,
        currency: str,
        notional: str,
        start_date: str,
        end_date: str,
        calendar: str
    ) -> None:
        """Create floating leg of OIS."""
        leg = etree.SubElement(swap_data, "LegData")

        # Leg type
        etree.SubElement(leg, "LegType").text = "Floating"

        # Payer flag
        etree.SubElement(leg, "Payer").text = str(payer).lower()

        # Currency
        etree.SubElement(leg, "Currency").text = currency

        # Notionals
        notionals = etree.SubElement(leg, "Notionals")
        etree.SubElement(notionals, "Notional").text = str(notional)

        # DayCounter
        day_counter = self._get_required("DayCounter")
        etree.SubElement(leg, "DayCounter").text = day_counter

        # PaymentConvention
        payment_conv = self._get_optional("PaymentConvention", DEFAULTS["PaymentConvention"])
        etree.SubElement(leg, "PaymentConvention").text = payment_conv

        # FloatingLegData
        floating_data = etree.SubElement(leg, "FloatingLegData")

        # Index (overnight index like EUR-EONIA, USD-SOFR)
        index = self._get_required("FloatingIndex")
        etree.SubElement(floating_data, "Index").text = index

        # Spreads
        spreads = etree.SubElement(floating_data, "Spreads")
        spread = self._get_optional("FloatingSpread", 0.0)
        etree.SubElement(spreads, "Spread").text = str(spread)

        # IsInArrears
        is_in_arrears = self._get_optional("IsInArrears", DEFAULTS["IsInArrears"])
        etree.SubElement(floating_data, "IsInArrears").text = str(is_in_arrears).lower()

        # FixingDays
        fixing_days = self._get_optional("FixingDays", DEFAULTS["FixingDays"])
        etree.SubElement(floating_data, "FixingDays").text = str(fixing_days)

        # ScheduleData
        tenor = self._get_required("Tenor")
        convention = self._get_optional("Convention", DEFAULTS["Convention"])
        self._create_schedule(
            leg,
            start_date,
            end_date,
            tenor,
            calendar,
            convention
        )

    def _create_schedule(
        self,
        leg: etree.Element,
        start_date: str,
        end_date: str,
        tenor: str,
        calendar: str,
        convention: str
    ) -> None:
        """Create schedule data for leg."""
        schedule_data = etree.SubElement(leg, "ScheduleData")
        rules = etree.SubElement(schedule_data, "Rules")

        etree.SubElement(rules, "StartDate").text = start_date
        etree.SubElement(rules, "EndDate").text = end_date
        etree.SubElement(rules, "Tenor").text = tenor
        etree.SubElement(rules, "Calendar").text = calendar
        etree.SubElement(rules, "Convention").text = convention
        etree.SubElement(rules, "TermConvention").text = convention
        etree.SubElement(rules, "Rule").text = DEFAULTS["Rule"]
