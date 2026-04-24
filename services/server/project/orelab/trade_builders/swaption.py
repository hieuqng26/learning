"""
Swaption trade builder.
"""

from lxml import etree
from .base import BaseTradeBuilder, ValidationResult
from ..utils import format_date_for_ore
from ..config import DEFAULTS


class SwaptionBuilder(BaseTradeBuilder):
    """
    Build Swaption trade XML.

    Supports European, Bermudan, and American exercise styles.
    Supports both Cash and Physical settlement.
    """

    REQUIRED_COLUMNS = [
        "TradeId", "CounterParty",
        # Option parameters
        "LongShort", "Style", "Settlement", "ExerciseDates",
        "PayerReceiver",
        # Underlying swap
        "Currency", "Notional", "StartDate", "EndDate",
        # Fixed leg
        "FixedRate", "FixedTenor", "FixedDayCounter",
        # Floating leg
        "FloatingIndex", "FloatingTenor", "FloatingDayCounter"
    ]

    def validate(self) -> ValidationResult:
        """Validate Swaption trade data."""
        result = ValidationResult()

        # Check required fields first
        self._validate_required_fields(result)
        if not result.is_valid:
            return result

        # Validate option parameters
        long_short = str(self.trade_data.get("LongShort", "")).capitalize()
        if long_short not in ["Long", "Short"]:
            result.add_error(f"Invalid LongShort: {self.trade_data.get('LongShort')} (expected Long or Short)")

        style = str(self.trade_data.get("Style", "")).capitalize()
        if style not in ["European", "Bermudan", "American"]:
            result.add_error(f"Invalid Style: {self.trade_data.get('Style')} (expected European, Bermudan, or American)")

        settlement = str(self.trade_data.get("Settlement", "")).capitalize()
        if settlement not in ["Cash", "Physical"]:
            result.add_error(f"Invalid Settlement: {self.trade_data.get('Settlement')} (expected Cash or Physical)")

        payer_receiver = str(self.trade_data.get("PayerReceiver", "")).capitalize()
        if payer_receiver not in ["Payer", "Receiver"]:
            result.add_error(f"Invalid PayerReceiver: {self.trade_data.get('PayerReceiver')} (expected Payer or Receiver)")

        # Validate exercise dates based on style
        exercise_dates_str = str(self.trade_data.get("ExerciseDates", ""))
        exercise_dates = [d.strip() for d in exercise_dates_str.split(',') if d.strip()]

        if style == "European" and len(exercise_dates) != 1:
            result.add_error(f"European swaption must have exactly 1 exercise date, got {len(exercise_dates)}")
        elif style == "American" and len(exercise_dates) != 2:
            result.add_error(f"American swaption must have exactly 2 exercise dates (start and end), got {len(exercise_dates)}")
        elif style == "Bermudan" and len(exercise_dates) < 2:
            result.add_error(f"Bermudan swaption must have at least 2 exercise dates, got {len(exercise_dates)}")

        # Validate each exercise date
        for date_str in exercise_dates:
            self._validate_date(date_str, "ExerciseDate", result)

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

        # Validate tenors
        self._validate_tenor(self.trade_data.get("FixedTenor"), "FixedTenor", result)
        self._validate_tenor(self.trade_data.get("FloatingTenor"), "FloatingTenor", result)

        # Validate premium if provided (all fields must be present together)
        premium_amount = self.trade_data.get("PremiumAmount")
        premium_currency = self.trade_data.get("PremiumCurrency")
        premium_pay_date = self.trade_data.get("PremiumPayDate")

        premium_fields = [premium_amount, premium_currency, premium_pay_date]
        premium_count = sum(1 for f in premium_fields if not self._is_empty(f))

        if premium_count > 0 and premium_count < 3:
            result.add_error("If premium is provided, all premium fields (PremiumAmount, PremiumCurrency, PremiumPayDate) must be specified")

        if not self._is_empty(premium_pay_date):
            self._validate_date(premium_pay_date, "PremiumPayDate", result)

        return result

    def build(self) -> etree.Element:
        """
        Build Swaption trade XML element.

        Returns:
            XML Element for Swaption trade
        """
        # Create root Trade element
        trade = etree.Element("Trade", id=self._get_required("TradeId"))

        # TradeType
        etree.SubElement(trade, "TradeType").text = "Swaption"

        # Envelope
        self._create_envelope(trade)

        # SwaptionData
        swaption_data = etree.SubElement(trade, "SwaptionData")

        # OptionData section
        self._create_option_data(swaption_data)

        # Get common parameters for legs
        currency = self._get_required("Currency")
        notional = self._get_required("Notional")
        start_date = format_date_for_ore(self._get_required("StartDate"))
        end_date = format_date_for_ore(self._get_required("EndDate"))
        calendar = self._get_optional("Calendar", DEFAULTS["Calendar"])
        payment_conv = self._get_optional("PaymentConvention", DEFAULTS["PaymentConvention"])

        # Determine payer flags based on PayerReceiver
        payer_receiver = self._get_required("PayerReceiver")
        is_payer = payer_receiver == "Payer"

        # Create Floating Leg (first leg in ORE swaption structure)
        self._create_floating_leg(
            swaption_data,
            payer=is_payer,  # Payer swaption pays floating
            currency=currency,
            notional=notional,
            start_date=start_date,
            end_date=end_date,
            calendar=calendar,
            payment_conv=payment_conv
        )

        # Create Fixed Leg (second leg in ORE swaption structure)
        self._create_fixed_leg(
            swaption_data,
            payer=not is_payer,  # Payer swaption receives fixed
            currency=currency,
            notional=notional,
            start_date=start_date,
            end_date=end_date,
            calendar=calendar,
            payment_conv=payment_conv
        )

        return trade

    def _create_option_data(self, swaption_data: etree.Element) -> None:
        """Create OptionData section for swaption."""
        option_data = etree.SubElement(swaption_data, "OptionData")

        # LongShort
        long_short = self._get_required("LongShort")
        etree.SubElement(option_data, "LongShort").text = str(long_short)

        # Style
        style = self._get_required("Style")
        etree.SubElement(option_data, "Style").text = str(style)

        # Settlement
        settlement = self._get_required("Settlement")
        etree.SubElement(option_data, "Settlement").text = str(settlement)

        # ExerciseDates
        exercise_dates_elem = etree.SubElement(option_data, "ExerciseDates")
        exercise_dates_str = str(self._get_required("ExerciseDates"))
        exercise_dates = [d.strip() for d in exercise_dates_str.split(',')]

        for date_str in exercise_dates:
            date_formatted = format_date_for_ore(date_str)
            etree.SubElement(exercise_dates_elem, "ExerciseDate").text = date_formatted

        # Premiums (optional)
        premium_amount = self._get_optional("PremiumAmount")
        if not self._is_empty(premium_amount):
            premiums_elem = etree.SubElement(option_data, "Premiums")
            premium_elem = etree.SubElement(premiums_elem, "Premium")

            etree.SubElement(premium_elem, "Amount").text = str(premium_amount)

            premium_currency = self._get_required("PremiumCurrency")
            etree.SubElement(premium_elem, "Currency").text = str(premium_currency)

            premium_pay_date = self._get_required("PremiumPayDate")
            etree.SubElement(premium_elem, "PayDate").text = format_date_for_ore(premium_pay_date)

    def _create_floating_leg(
        self,
        swaption_data: etree.Element,
        payer: bool,
        currency: str,
        notional: str,
        start_date: str,
        end_date: str,
        calendar: str,
        payment_conv: str
    ) -> None:
        """Create floating leg of swaption."""
        leg = etree.SubElement(swaption_data, "LegData")

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

        # IsInArrears (optional)
        is_in_arrears = self._get_optional("IsInArrears", DEFAULTS["IsInArrears"])
        etree.SubElement(floating_data, "IsInArrears").text = str(is_in_arrears).lower()

        # FixingDays (optional)
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

    def _create_fixed_leg(
        self,
        swaption_data: etree.Element,
        payer: bool,
        currency: str,
        notional: str,
        start_date: str,
        end_date: str,
        calendar: str,
        payment_conv: str
    ) -> None:
        """Create fixed leg of swaption."""
        leg = etree.SubElement(swaption_data, "LegData")

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
