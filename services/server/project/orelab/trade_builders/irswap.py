"""
Interest Rate Swap trade builder.
"""

from lxml import etree
from .base import BaseTradeBuilder, ValidationResult
from ..utils import format_date_for_ore
from ..config import DEFAULTS


class InterestRateSwapBuilder(BaseTradeBuilder):
    """
    Build Interest Rate Swap trade XML.

    Optional fields:
    - FloatingSpread (default: 0.0)
    - Calendar (default: TARGET)
    - PaymentConvention (default: MF)
    - FixingDays (default: 2)
    """

    REQUIRED_COLUMNS = [
        "TradeId", "CounterParty", "Currency", "Notional",
        "StartDate", "EndDate", "FixedPayer",
        "FixedRate", "FixedTenor", "FixedDayCounter",
        "FloatingIndex", "FloatingTenor", "FloatingDayCounter"
    ]

    def validate(self) -> ValidationResult:
        """Validate Interest Rate Swap trade data."""
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

        # Validate fixed rate
        try:
            fixed_rate = float(self.trade_data.get("FixedRate", 0))
            if fixed_rate < -1 or fixed_rate > 1:
                result.add_warning(f"Unusual fixed rate: {fixed_rate} (expected range: -1 to 1)")
        except (ValueError, TypeError):
            result.add_error(f"Invalid fixed rate: {self.trade_data.get('FixedRate')}")

        # Validate fixed payer
        fixed_payer = str(self.trade_data.get("FixedPayer", "")).lower()
        if fixed_payer not in ["true", "false", "1", "0", "yes", "no"]:
            result.add_error(f"Invalid FixedPayer: {self.trade_data.get('FixedPayer')} (expected True or False)")

        # Validate tenors
        self._validate_tenor(self.trade_data.get("FixedTenor"), "FixedTenor", result)
        self._validate_tenor(self.trade_data.get("FloatingTenor"), "FloatingTenor", result)

        return result

    def build(self) -> etree.Element:
        """
        Build Interest Rate Swap trade XML element.

        Returns:
            XML Element for IRS trade
        """
        # Create root Trade element
        trade = etree.Element("Trade", id=self._get_required("TradeId"))

        # TradeType
        etree.SubElement(trade, "TradeType").text = "Swap"

        # Envelope
        self._create_envelope(trade)

        # SwapData
        swap_data = etree.SubElement(trade, "SwapData")

        # Determine if we're paying or receiving fixed
        fixed_payer = self._get_required("FixedPayer")
        is_payer = str(fixed_payer).lower() == "true"

        # Get common parameters
        currency = self._get_required("Currency")
        notional = self._get_required("Notional")
        start_date = format_date_for_ore(self._get_required("StartDate"))
        end_date = format_date_for_ore(self._get_required("EndDate"))
        calendar = self._get_optional("Calendar", DEFAULTS["Calendar"])

        # Create Fixed Leg
        self._create_fixed_leg(
            swap_data,
            payer=is_payer,
            currency=currency,
            notional=notional,
            start_date=start_date,
            end_date=end_date,
            calendar=calendar
        )

        # Create Floating Leg
        self._create_floating_leg(
            swap_data,
            payer=not is_payer,  # Opposite of fixed leg
            currency=currency,
            notional=notional,
            start_date=start_date,
            end_date=end_date,
            calendar=calendar
        )

        return trade

    def _create_fixed_leg(
        self,
        swap_data: etree.Element,
        payer: bool,
        currency: str,
        notional: str,
        start_date: str,
        end_date: str,
        calendar: str
    ) -> None:
        """Create fixed leg of swap."""
        leg = etree.SubElement(swap_data, "LegData")

        # Leg type
        etree.SubElement(leg, "LegType").text = "Fixed"

        # Payer flag
        etree.SubElement(leg, "Payer").text = str(payer).lower()

        # Currency
        etree.SubElement(leg, "Currency").text = currency

        # Notionals
        notionals = etree.SubElement(leg, "Notionals")
        etree.SubElement(notionals, "Notional").text = str(notional)

        # DayCounter
        day_counter = self._get_required("FixedDayCounter")
        etree.SubElement(leg, "DayCounter").text = day_counter

        # PaymentConvention
        payment_conv = self._get_optional("PaymentConvention", DEFAULTS["PaymentConvention"])
        etree.SubElement(leg, "PaymentConvention").text = payment_conv

        # FixedLegData
        fixed_data = etree.SubElement(leg, "FixedLegData")
        rates = etree.SubElement(fixed_data, "Rates")
        fixed_rate = self._get_required("FixedRate")
        etree.SubElement(rates, "Rate").text = str(fixed_rate)

        # ScheduleData
        self._create_schedule(
            leg,
            start_date,
            end_date,
            self._get_required("FixedTenor"),
            calendar,
            payment_conv
        )

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
        """Create floating leg of swap."""
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
        day_counter = self._get_required("FloatingDayCounter")
        etree.SubElement(leg, "DayCounter").text = day_counter

        # PaymentConvention
        payment_conv = self._get_optional("PaymentConvention", DEFAULTS["PaymentConvention"])
        etree.SubElement(leg, "PaymentConvention").text = payment_conv

        # FloatingLegData
        floating_data = etree.SubElement(leg, "FloatingLegData")

        # Index
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
        self._create_schedule(
            leg,
            start_date,
            end_date,
            self._get_required("FloatingTenor"),
            calendar,
            payment_conv
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
